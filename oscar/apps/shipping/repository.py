from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping.methods import (
    Free, NoShippingRequired, OfferDiscount)

from decimal import Decimal as D


class Repository(object):
    """
    Repository class responsible for returning ShippingMethod
    objects for a given user, basket etc
    """
    methods = (Free(),)

    def get_shipping_methods(self, user, basket, shipping_addr=None,
                             request=None, **kwargs):
        """
        Return a list of all applicable shipping method objects
        for a given basket.

        We default to returning the Method models that have been defined but
        this behaviour can easily be overridden by subclassing this class
        and overriding this method.
        """
        return self.prime_methods(basket, self.methods)

    def get_default_shipping_method(self, user, basket, shipping_addr=None,
                                    request=None, **kwargs):
        """
        Return a 'default' shipping method to show on the basket page to give
        the customer an indication of what their order will cost.
        """
        methods = self.get_shipping_methods(
            user, basket, shipping_addr, request, **kwargs)
        if len(methods) == 0:
            raise ImproperlyConfigured(
                _("You need to define some shipping methods"))

        # Choose the cheapest method by default
        return min(methods, key=lambda method: method.basket_charge_incl_tax())

    def prime_methods(self, basket, methods):
        """
        Prime a list of shipping method instances

        This involves injecting the basket instance into each and adding any
        discount wrappers.
        """
        return [self.prime_method(basket, method) for
                method in methods]

    def prime_method(self, basket, method):
        """
        Prime an individual method instance
        """
        method.set_basket(basket)
        # If the basket has a shipping offer, wrap the shipping method with a
        # decorating class that applies the offer discount to the shipping
        # charge.
        if basket.offer_applications.shipping_discounts:
            # We assume there is only one shipping discount available
            discount = basket.offer_applications.shipping_discounts[0]
            if method.basket_charge_incl_tax > D('0.00'):
                return OfferDiscount(method, discount['offer'])
        return method

    def find_by_code(self, code, basket):
        """
        Return the appropriate Method object for the given code
        """
        for method in self.methods:
            if method.code == code:
                return self.prime_method(basket, method)

        # Check for NoShippingRequired as that is a special case
        if code == NoShippingRequired.code:
            return self.prime_method(basket, NoShippingRequired())
