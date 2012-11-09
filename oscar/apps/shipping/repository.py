from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _


from oscar.apps.shipping.methods import (
    Free, NoShippingRequired, OfferDiscount)


class Repository(object):
    """
    Repository class responsible for returning ShippingMethod
    objects for a given user, basket etc
    """

    def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
        """
        Return a list of all applicable shipping method objects
        for a given basket.

        We default to returning the Method models that have been defined but
        this behaviour can easily be overridden by subclassing this class
        and overriding this method.
        """
        methods = [Free()]
        return self.prime_methods(basket, methods)

    def get_default_shipping_method(self, user, basket, shipping_addr=None,
                                    **kwargs):
        """
        Return a 'default' shipping method to show on the basket page to give
        the customer an indication of what their order will cost.
        """
        methods = self.get_shipping_methods(
            user, basket, shipping_addr, **kwargs)
        if len(methods) == 0:
            raise ImproperlyConfigured(
                _("You need to define some shipping methods"))
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
        if basket.shipping_offer:
            return OfferDiscount(method, basket.shipping_offer)
        return method

    def find_by_code(self, code, basket):
        """
        Return the appropriate Method object for the given code
        """
        known_methods = [Free, NoShippingRequired]
        for klass in known_methods:
            if code == getattr(klass, 'code'):
                return self.prime_method(basket, klass())
        return None
