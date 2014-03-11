from django.contrib import messages
from django import http
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model, get_class
from . import exceptions

Repository = get_class('shipping.repository', 'Repository')
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
    # This should be list of method names that get executed before the normal
    # flow of the view.
    pre_conditions = None

    def dispatch(self, request, *args, **kwargs):
        # Assign the checkout session manager so it's available in all checkout
        # views.
        self.checkout_session = CheckoutSessionData(request)

        # Enforce any pre-conditions for the view.
        try:
            self.check_preconditions(request)
        except exceptions.FailedPreCondition, e:
            messages.error(request, e.message)
            return http.HttpResponseRedirect(e.url)

        return super(CheckoutSessionMixin, self).dispatch(
            request, *args, **kwargs)

    def check_preconditions(self, request):
        if self.pre_conditions is None:
            return
        for method_name in self.pre_conditions:
            if not hasattr(self, method_name):
                raise ImproperlyConfigured(
                    "There is no method '%s' to call as a pre-condition" % (
                        method_name))
            getattr(self, method_name)(request)

    # Re-usable pre-condition validators

    def check_basket_is_not_empty(self, request):
        if request.basket.is_empty:
            raise exceptions.FailedPreCondition(
                url=reverse('basket:summary'),
                message=_(
                    "You need to add some items to your basket to checkout")
            )

    def check_user_email_is_captured(self, request):
        if not request.user.is_authenticated() \
                and not self.checkout_session.get_guest_email():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:index'),
                message=_(
                    "Please either sign in or enter your email address")
            )

    def check_basket_requires_shipping(self, request):
        # Check to see that a shipping address is actually required.  It may
        # not be if the basket is purely downloads
        if not request.basket.is_shipping_required():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-method'),
                message=_(
                    "Your basket does not require a shipping"
                    "address to be submitted")
            )

    def check_shipping_data_is_captured(self, request):
        if not request.basket.is_shipping_required():
            return

        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-address'),
                message=_("Please choose a shipping address")
            )

        # Check that shipping method has been set
        if not self.checkout_session.is_shipping_method_set(
                self.request.basket):
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-address'),
                message=_("Please choose a shipping method")
            )

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
        addr_id = self.checkout_session.user_address_id()
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
        stored in the session is still valid for the shippinga address.
        """
        code = self.checkout_session.shipping_method_code(basket)
        methods = Repository().get_shipping_methods(
            user=self.request.user, basket=basket,
            shipping_addr=shipping_address, request=self.request)
        for method in methods:
            if method.code == code:
                return method

    def get_order_totals(self, basket, shipping_method, **kwargs):
        """
        Returns the total for the order with and without tax (as a tuple)
        """
        return OrderTotalCalculator(self.request).calculate(
            basket, shipping_method, **kwargs)
