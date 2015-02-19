from oscar.core.loading import get_model, get_class


CheckoutSessionData = get_class('checkout.utils', 'CheckoutSessionData')
OrderTotalCalculator = get_class('checkout.calculators',
                                 'OrderTotalCalculator')
Repository = get_class('shipping.repository', 'Repository')
ShippingAddress = get_model('order', 'ShippingAddress')
BillingAddress = get_model('order', 'BillingAddress')
UserAddress = get_model('address', 'UserAddress')


class CheckoutSessionMixin(object):
    """
    All checkout views subclass this mixin. It ensures that all relevant
    checkout information is available in the template context.
    """
    def dispatch(self, request, *args, **kwargs):
        # Assign the checkout session manager so it's available in all checkout
        # views.
        self.checkout_session = CheckoutSessionData(request)

        return super(CheckoutSessionMixin, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Use the proposed submission as template context data.  Flatten the
        # order kwargs so they are easily available too.
        ctx = self.build_submission(**kwargs)
        ctx.update(kwargs)
        ctx.update(ctx['order_kwargs'])
        return ctx

    def freeze_for_external_payment(self, clerk):
        self.checkout_session.set_order_number(clerk.order_number)

        # Freeze the basket so it cannot be manipulated while the customer is
        # completing payment on a 3rd party site.  If your payment fails, then
        # the basket will need to be "unfrozen".
        clerk.basket.freeze()

        # Store a reference to the basket in the session so that we know which
        # basket to thaw if we get an unsuccessful payment response when
        # redirecting to a 3rd party site.
        self.checkout_session.set_submitted_basket(clerk.basket)

    def build_submission(self, **kwargs):
        """
        Return a dict of data that contains everything required for an order
        submission.  This includes payment details (if any).

        This can be the right place to perform tax lookups and apply them to
        the basket.
        """
        basket = kwargs.get('basket', self.request.basket)
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(
            basket, shipping_address)
        billing_address = self.get_billing_address(shipping_address)

        if not shipping_method:
            total = shipping_charge = None
        else:
            shipping_charge = shipping_method.calculate(basket)
            total = self.get_order_totals(
                basket, shipping_charge=shipping_charge)

        submission = {
            'user': self.request.user,
            'basket': basket,
            'shipping_address': shipping_address,
            'shipping_method': shipping_method,
            'shipping_charge': shipping_charge,
            'billing_address': billing_address,
            'order_total': total,
            'order_kwargs': {},
            'payment_kwargs': {}}

        # If there is a billing address, add it to the payment kwargs as calls
        # to payment gateways generally require the billing address. Note, that
        # it normally makes sense to pass the form instance that captures the
        # billing address information. That way, if payment fails, you can
        # render bound forms in the template to make re-submission easier.
        if billing_address:
            submission['payment_kwargs']['billing_address'] = billing_address

        # Allow overrides to be passed in
        submission.update(kwargs)

        # Set guest email after overrides as we need to update the order_kwargs
        # entry.
        if (not submission['user'].is_authenticated() and
                'guest_email' not in submission['order_kwargs']):
            email = self.checkout_session.get_guest_email()
            submission['order_kwargs']['guest_email'] = email
        return submission

    def get_shipping_address(self, basket):
        """
        Return the (unsaved) shipping address for this checkout session.

        If the shipping address was entered manually, then we instantiate a
        ``ShippingAddress`` model with the appropriate form data (which is
        saved in the session).

        If the shipping address was selected from the user's address book,
        then we convert the ``UserAddress`` to a ``ShippingAddress``.

        The ``ShippingAddress`` instance is not saved as sometimes you need a
        shipping address instance before the order is placed.  For example, if
        you are submitting fraud information as part of a payment request.

        The ``OrderPlacementMixin.create_shipping_address`` method is
        responsible for saving a shipping address when an order is placed.
        """
        if not basket.is_shipping_required():
            return None

        addr_data = self.checkout_session.new_shipping_address_fields()
        if addr_data:
            # Load address data into a blank shipping address model
            return ShippingAddress(**addr_data)
        addr_id = self.checkout_session.shipping_user_address_id()
        if addr_id:
            try:
                address = UserAddress._default_manager.get(pk=addr_id)
            except UserAddress.DoesNotExist:
                # An address was selected but now it has disappeared.  This can
                # happen if the customer flushes their address book midway
                # through checkout.  No idea why they would do this but it can
                # happen.  Checkouts are highly vulnerable to race conditions
                # like this.
                return None
            else:
                # Copy user address data into a blank shipping address instance
                shipping_addr = ShippingAddress()
                address.populate_alternative_model(shipping_addr)
                return shipping_addr

    def get_shipping_method(self, basket, shipping_address=None):
        """
        Return the selected shipping method instance from this checkout session

        The shipping address is passed as we need to check that the method
        stored in the session is still valid for the shipping address.
        """
        code = self.checkout_session.shipping_method_code(basket)
        methods = self.get_available_shipping_methods(basket, shipping_address)
        for method in methods:
            if method.code == code:
                return method

    def get_available_shipping_methods(self, basket, shipping_address=None):
        """
        Returns all applicable shipping method objects for a given basket.
        """
        # Shipping methods can depend on the user, the contents of the basket
        # and the shipping address (so we pass all these things to the
        # repository).  I haven't come across a scenario that doesn't fit this
        # system.
        return Repository().get_shipping_methods(
            basket, shipping_address, user=self.request.user,
            request=self.request)

    def get_billing_address(self, shipping_address):
        """
        Return an unsaved instance of the billing address (if one exists)

        This method only returns a billing address if the session has been used
        to store billing address information. It's also possible to capture
        billing address information as part of the payment details forms, which
        never get stored in the session. In that circumstance, the billing
        address can be set directly in the build_submission dict (see Oscar's
        demo site for an example of this approach).
        """
        if not self.checkout_session.is_billing_address_set():
            return None
        if self.checkout_session.is_billing_address_same_as_shipping():
            if shipping_address:
                address = BillingAddress()
                shipping_address.populate_alternative_model(address)
                return address

        addr_data = self.checkout_session.new_billing_address_fields()
        if addr_data:
            # A new billing address has been entered - load address data into a
            # blank billing address model.
            return BillingAddress(**addr_data)

        addr_id = self.checkout_session.billing_user_address_id()
        if addr_id:
            # An address from the user's address book has been selected as the
            # billing address - load it and convert it into a billing address
            # instance.
            try:
                user_address = UserAddress._default_manager.get(pk=addr_id)
            except UserAddress.DoesNotExist:
                # An address was selected but now it has disappeared.  This can
                # happen if the customer flushes their address book midway
                # through checkout.  No idea why they would do this but it can
                # happen.  Checkouts are highly vulnerable to race conditions
                # like this.
                return None
            else:
                # Copy user address data into a blank shipping address instance
                billing_address = BillingAddress()
                user_address.populate_alternative_model(billing_address)
                return billing_address

    def get_order_totals(self, basket, shipping_charge, **kwargs):
        """
        Returns the total for the order with and without tax
        """
        return OrderTotalCalculator(self.request).calculate(
            basket, shipping_charge, **kwargs)
