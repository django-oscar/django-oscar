from django.db.models import get_model

from oscar.core.loading import get_class

OrderTotalCalculator = get_class(
    'checkout.calculators', 'OrderTotalCalculator')
CheckoutSessionData = get_class(
    'checkout.utils', 'CheckoutSessionData')
ShippingAddress = get_model('order', 'ShippingAddress')
UserAddress = get_model('address', 'UserAddress')


class CheckoutSessionMixin(object):
    """
    Mixin to provide common functionality shared between checkout views.
    """

    def dispatch(self, request, *args, **kwargs):
        self.checkout_session = CheckoutSessionData(request)
        return super(CheckoutSessionMixin, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Assign common template variables to the context.
        """
        ctx = super(CheckoutSessionMixin, self).get_context_data(**kwargs)

        basket = self.request.basket
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(
            basket, shipping_address)

        ctx['shipping_address'] = shipping_address
        ctx['shipping_method'] = shipping_method
        if basket and shipping_method:
            ctx['order_total'] = self.get_order_totals(basket, shipping_method)

        return ctx

    def get_shipping_address(self, basket):
        """
        Return the (unsaved) shipping address for this checkout session.

        If the shipping address was entered manually, then we instanciate a
        ShippingAddress model with the appropriate form data.

        If the shipping address was selected from the user's address book,
        then we convert the UserAddress to a ShippingAddress.

        The ShippingAddress instance is not saved as sometimes you need a
        shipping address instance before the order is placed.  For example, if
        you are submitting fraud information as part of a payment request.

        The create_shipping_address method is responsible for saving a shipping
        address when an order is placed.
        """
        if not basket.is_shipping_required():
            return None

        addr_data = self.checkout_session.new_shipping_address_fields()
        if addr_data:
            # Load address data into a blank address model
            return ShippingAddress(**addr_data)
        addr_id = self.checkout_session.user_address_id()
        if addr_id:
            try:
                address = UserAddress._default_manager.get(pk=addr_id)
            except UserAddress.DoesNotExist:
                # This can happen if you reset all your tables and you still
                # have session data that refers to addresses that no longer
                # exist.
                pass
            else:
                shipping_addr = ShippingAddress()
                address.populate_alternative_model(shipping_addr)
                return shipping_addr
        return None

    def get_shipping_method(self, basket, shipping_address=None, **kwargs):
        """
        Return the selected shipping method instance from this checkout session

        The shipping address is passed as this is sometimes needed to determine
        the tax applicable on a shipping method.
        """
        return self.checkout_session.shipping_method(basket)

    def get_order_totals(self, basket, shipping_method, **kwargs):
        """
        Returns the total for the order with and without tax (as a tuple)
        """
        return OrderTotalCalculator(self.request).calculate(
            basket, shipping_method, **kwargs)
