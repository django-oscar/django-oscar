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
        Return the shipping address for this checkout session.

        This could either be a ShippingAddress model which has been
        pre-populated (not saved), or a UserAddress model which will
        need converting into a ShippingAddress model at submission
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
                return UserAddress._default_manager.get(pk=addr_id)
            except UserAddress.DoesNotExist:
                # This can happen if you reset all your tables and you still
                # have session data that refers to addresses that no longer
                # exist.
                pass
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
