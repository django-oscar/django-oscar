from decimal import Decimal as D

from django import http
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from oscar.core import prices
from oscar.core.loading import get_class, get_model

from . import exceptions

Repository = get_class('shipping.repository', 'Repository')
SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")
OrderTotalCalculator = get_class(
    'checkout.calculators', 'OrderTotalCalculator')
CheckoutSessionData = get_class(
    'checkout.utils', 'CheckoutSessionData')
ShippingAddress = get_model('order', 'ShippingAddress')
BillingAddress = get_model('order', 'BillingAddress')
UserAddress = get_model('address', 'UserAddress')


class CheckoutSessionMixin(object):
    """
    Mixin to provide common functionality shared between checkout views.

    All checkout views subclass this mixin. It ensures that all relevant
    checkout information is available in the template context.
    """

    # A pre-condition is a condition that MUST be met in order for a view
    # to be available. If it isn't then the customer should be redirected
    # to a view *earlier* in the chain.
    # pre_conditions is a list of method names that get executed before the
    # normal flow of the view. Each method should check some condition has been
    # met. If not, then an exception is raised that indicates the URL the
    # customer will be redirected to.

    pre_conditions = None

    # A *skip* condition is a condition that MUST NOT be met in order for a
    # view to be available. If the condition is met, this means the view MUST
    # be skipped and the customer should be redirected to a view *later* in
    # the chain.
    # Skip conditions work similar to pre-conditions, and get evaluated after
    # pre-conditions have been evaluated.
    skip_conditions = None

    def dispatch(self, request, *args, **kwargs):
        # Assign the checkout session manager so it's available in all checkout
        # views.
        self.checkout_session = CheckoutSessionData(request)

        # Enforce any pre-conditions for the view.
        try:
            self.check_pre_conditions(request)
        except exceptions.FailedPreCondition as e:
            for message in e.messages:
                messages.warning(request, message)
            return http.HttpResponseRedirect(e.url)

        # Check if this view should be skipped
        try:
            self.check_skip_conditions(request)
        except exceptions.PassedSkipCondition as e:
            return http.HttpResponseRedirect(e.url)

        return super().dispatch(
            request, *args, **kwargs)

    def check_pre_conditions(self, request):
        pre_conditions = self.get_pre_conditions(request)
        for method_name in pre_conditions:
            if not hasattr(self, method_name):
                raise ImproperlyConfigured(
                    "There is no method '%s' to call as a pre-condition" % (
                        method_name))
            getattr(self, method_name)(request)

    def get_pre_conditions(self, request):
        """
        Return the pre-condition method names to run for this view
        """
        if self.pre_conditions is None:
            return []
        return self.pre_conditions

    def check_skip_conditions(self, request):
        skip_conditions = self.get_skip_conditions(request)
        for method_name in skip_conditions:
            if not hasattr(self, method_name):
                raise ImproperlyConfigured(
                    "There is no method '%s' to call as a skip-condition" % (
                        method_name))
            getattr(self, method_name)(request)

    def get_skip_conditions(self, request):
        """
        Return the skip-condition method names to run for this view
        """
        if self.skip_conditions is None:
            return []
        return self.skip_conditions

    # Re-usable pre-condition validators

    def check_basket_is_not_empty(self, request):
        if request.basket.is_empty:
            raise exceptions.FailedPreCondition(
                url=reverse('basket:summary'),
                message=_(
                    "You need to add some items to your basket to checkout")
            )

    def check_basket_is_valid(self, request):
        """
        Check that the basket is permitted to be submitted as an order. That
        is, all the basket lines are available to buy - nothing has gone out of
        stock since it was added to the basket.
        """
        messages = []
        strategy = request.strategy
        for line in request.basket.all_lines():
            result = strategy.fetch_for_line(line)
            is_permitted, reason = result.availability.is_purchase_permitted(
                line.quantity)
            if not is_permitted:
                # Create a more meaningful message to show on the basket page
                msg = _(
                    "'%(title)s' is no longer available to buy (%(reason)s). "
                    "Please adjust your basket to continue"
                ) % {
                    'title': line.product.get_title(),
                    'reason': reason}
                messages.append(msg)
        if messages:
            raise exceptions.FailedPreCondition(
                url=reverse('basket:summary'),
                messages=messages
            )

    def check_user_email_is_captured(self, request):
        if not request.user.is_authenticated \
                and not self.checkout_session.get_guest_email():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:index'),
                message=_(
                    "Please either sign in or enter your email address")
            )

    def check_shipping_data_is_captured(self, request):
        if not request.basket.is_shipping_required():
            # Even without shipping being required, we still need to check that
            # a shipping method code has been set.
            if not self.checkout_session.is_shipping_method_set(
                    self.request.basket):
                raise exceptions.FailedPreCondition(
                    url=reverse('checkout:shipping-method'),
                )
            return

        # Basket requires shipping: check address and method are captured and
        # valid.
        self.check_a_valid_shipping_address_is_captured()
        self.check_a_valid_shipping_method_is_captured()

    def check_a_valid_shipping_address_is_captured(self):
        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-address'),
                message=_("Please choose a shipping address")
            )

        # Check that the previously chosen shipping address is still valid
        shipping_address = self.get_shipping_address(
            basket=self.request.basket)
        if not shipping_address:
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-address'),
                message=_("Your previously chosen shipping address is "
                          "no longer valid.  Please choose another one")
            )

    def check_a_valid_shipping_method_is_captured(self):
        # Check that shipping method has been set
        if not self.checkout_session.is_shipping_method_set(
                self.request.basket):
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-method'),
                message=_("Please choose a shipping method")
            )

        # Check that a *valid* shipping method has been set
        shipping_address = self.get_shipping_address(
            basket=self.request.basket)
        shipping_method = self.get_shipping_method(
            basket=self.request.basket,
            shipping_address=shipping_address)
        if not shipping_method:
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-method'),
                message=_("Your previously chosen shipping method is "
                          "no longer valid.  Please choose another one")
            )

    def check_payment_data_is_captured(self, request):
        # We don't collect payment data by default so we don't have anything to
        # validate here. If your shop requires forms to be submitted on the
        # payment details page, then override this method to check that the
        # relevant data is available. Often just enforcing that the preview
        # view is only accessible from a POST request is sufficient.
        pass

    # Re-usable skip conditions

    def skip_unless_basket_requires_shipping(self, request):
        # Check to see that a shipping address is actually required.  It may
        # not be if the basket is purely downloads
        if not request.basket.is_shipping_required():
            raise exceptions.PassedSkipCondition(
                url=reverse('checkout:shipping-method')
            )

    def skip_unless_payment_is_required(self, request):
        # Check to see if payment is actually required for this order.
        shipping_address = self.get_shipping_address(request.basket)
        shipping_method = self.get_shipping_method(
            request.basket, shipping_address)
        if shipping_method:
            shipping_charge = shipping_method.calculate(request.basket)
        else:
            # It's unusual to get here as a shipping method should be set by
            # the time this skip-condition is called. In the absence of any
            # other evidence, we assume the shipping charge is zero.
            shipping_charge = prices.Price(
                currency=request.basket.currency, excl_tax=D('0.00'),
                tax=D('0.00')
            )

        surcharges = SurchargeApplicator(request).get_applicable_surcharges(
            basket=request.basket, shipping_charge=shipping_charge
        )
        total = self.get_order_totals(request.basket, shipping_charge, surcharges)
        if total.excl_tax == D('0.00'):
            raise exceptions.PassedSkipCondition(
                url=reverse('checkout:preview')
            )

    # Helpers

    def get_context_data(self, **kwargs):
        # Use the proposed submission as template context data.  Flatten the
        # order kwargs so they are easily available too.
        ctx = super().get_context_data()
        ctx.update(self.build_submission(**kwargs))
        ctx.update(kwargs)
        ctx.update(ctx['order_kwargs'])
        return ctx

    def build_submission(self, **kwargs):
        """
        Return a dict of data that contains everything required for an order
        submission.  This includes payment details (if any).

        This can be the right place to perform tax lookups and apply them to
        the basket.
        """
        # Pop the basket if there is one, because we pass it as a positional
        # argument to methods below
        basket = kwargs.pop('basket', self.request.basket)
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(
            basket, shipping_address)
        billing_address = self.get_billing_address(shipping_address)
        submission = {
            'user': self.request.user,
            'basket': basket,
            'shipping_address': shipping_address,
            'shipping_method': shipping_method,
            'billing_address': billing_address,
            'order_kwargs': {},
            'payment_kwargs': {}
        }

        if not shipping_method:
            total = shipping_charge = surcharges = None
        else:
            shipping_charge = shipping_method.calculate(basket)
            surcharges = SurchargeApplicator(self.request, submission).get_applicable_surcharges(
                self.request.basket, shipping_charge=shipping_charge
            )
            total = self.get_order_totals(
                basket, shipping_charge=shipping_charge, surcharges=surcharges, **kwargs)

        submission["shipping_charge"] = shipping_charge
        submission["order_total"] = total
        submission['surcharges'] = surcharges

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
        user = submission['user']
        if (not user.is_authenticated
                and 'guest_email' not in submission['order_kwargs']):
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

    def get_shipping_method(self, basket, shipping_address=None, **kwargs):
        """
        Return the selected shipping method instance from this checkout session

        The shipping address is passed as we need to check that the method
        stored in the session is still valid for the shipping address.
        """
        code = self.checkout_session.shipping_method_code(basket)
        methods = Repository().get_shipping_methods(
            basket=basket, user=self.request.user,
            shipping_addr=shipping_address, request=self.request)
        for method in methods:
            if method.code == code:
                return method

    def get_billing_address(self, shipping_address):
        """
        Return an unsaved instance of the billing address (if one exists)

        This method only returns a billing address if the session has been used
        to store billing address information. It's also possible to capture
        billing address information as part of the payment details forms, which
        never get stored in the session. In that circumstance, the billing
        address can be set directly in the build_submission dict.
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

    def get_order_totals(self, basket, shipping_charge, surcharges=None, **kwargs):
        """
        Returns the total for the order with and without tax
        """
        return OrderTotalCalculator(self.request).calculate(
            basket, shipping_charge, surcharges, **kwargs)
