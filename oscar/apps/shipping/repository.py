from decimal import Decimal as D

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping import methods


class Repository(object):
    """
    Repository class responsible for returning ShippingMethod
    objects for a given user, basket etc
    """

    # We default to just free shipping. Customise this class and override this
    # property to add your own shipping methods.
    methods = (methods.Free,)

    # API

    def get_shipping_methods(self, basket, user=None, shipping_addr=None,
                             request=None, **kwargs):
        """
        Return a list of all applicable shipping method objects
        for a given basket, address etc.

        We default to returning the ``Method`` models that have been defined
        but this behaviour can easily be overridden by subclassing this class
        and overriding this method.
        """
        if not basket.is_shipping_required():
            return [methods.NoShippingRequired()]
        methods_ = [klass() for klass in self.methods]
        return self.prime_methods(basket, methods_)

    def get_default_shipping_method(self, user, basket, shipping_addr=None,
                                    request=None, **kwargs):
        """
        Return a 'default' shipping method to show on the basket page to give
        the customer an indication of what their order will cost.
        """
        shipping_methods = self.get_shipping_methods(
            basket, user, shipping_addr=shipping_addr,
            request=request, **kwargs)
        if len(shipping_methods) == 0:
            raise ImproperlyConfigured(
                _("You need to define some shipping methods"))

        # Assume first returned method is default
        return shipping_methods[0]

    # Helpers

    def prime_methods(self, basket, methods):
        """
        Prime a list of shipping method instances

        This involves injecting the basket instance into each and adding any
        discount wrappers.
        """
        return [self.prime_method(basket, method) for method in methods]

    def prime_method(self, basket, method):
        """
        Prime an individual method instance
        """
        if not basket.has_shipping_discounts:
            return method

        # If the basket has qualified for shipping discount, wrap the shipping
        # method with a decorating class that applies the offer discount to the
        # shipping charge.
        discount = basket.shipping_discounts[0]
        charge = method.calculate(basket)
        if charge.excl_tax == D('0.00'):
            # No need to wrap zero shipping charges
            return method

        if charge.is_tax_known:
            return methods.TaxInclusiveOfferDiscount(
                method, discount['offer'])
        else:
            # When returning a tax exclusive discount, it is assumed
            # that this will be used to calculate taxes which will then
            # be assigned directly to the method instance.
            return methods.TaxExclusiveOfferDiscount(
                method, discount['offer'])
