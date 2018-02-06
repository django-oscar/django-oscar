from decimal import Decimal as D

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_classes

(Free, NoShippingRequired,
 TaxExclusiveOfferDiscount, TaxInclusiveOfferDiscount) \
    = get_classes('shipping.methods', ['Free', 'NoShippingRequired',
                                       'TaxExclusiveOfferDiscount', 'TaxInclusiveOfferDiscount'])


class Repository(object):
    """
    Repository class responsible for returning ShippingMethod
    objects for a given user, basket etc
    """

    # We default to just free shipping. Customise this class and override this
    # property to add your own shipping methods. This should be a list of
    # instantiated shipping methods.
    methods = (Free(),)

    # API

    def get_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        """
        Return a list of all applicable shipping method instances for a given
        basket, address etc.
        """
        if not basket.is_shipping_required():
            # Special case! Baskets that don't require shipping get a special
            # shipping method.
            return [NoShippingRequired()]

        methods = self.get_available_shipping_methods(
            basket=basket, shipping_addr=shipping_addr, **kwargs)
        if basket.has_shipping_discounts:
            methods = self.apply_shipping_offers(basket, methods)
        return methods

    def get_default_shipping_method(self, basket, shipping_addr=None,
                                    **kwargs):
        """
        Return a 'default' shipping method to show on the basket page to give
        the customer an indication of what their order will cost.
        """
        shipping_methods = self.get_shipping_methods(
            basket, shipping_addr=shipping_addr, **kwargs)
        if len(shipping_methods) == 0:
            raise ImproperlyConfigured(
                _("You need to define some shipping methods"))

        # Assume first returned method is default
        return shipping_methods[0]

    # Helpers

    def get_available_shipping_methods(
            self, basket, shipping_addr=None, **kwargs):
        """
        Return a list of all applicable shipping method instances for a given
        basket, address etc. This method is intended to be overridden.
        """
        return self.methods

    def apply_shipping_offers(self, basket, methods):
        """
        Apply shipping offers to the passed set of methods
        """
        # We default to only applying the first shipping discount.
        offer = basket.shipping_discounts[0]['offer']
        return [self.apply_shipping_offer(basket, method, offer)
                for method in methods]

    def apply_shipping_offer(self, basket, method, offer):
        """
        Wrap a shipping method with an offer discount wrapper (as long as the
        shipping charge is non-zero).
        """
        # If the basket has qualified for shipping discount, wrap the shipping
        # method with a decorating class that applies the offer discount to the
        # shipping charge.
        charge = method.calculate(basket)
        if charge.excl_tax == D('0.00'):
            # No need to wrap zero shipping charges
            return method

        if charge.is_tax_known:
            return TaxInclusiveOfferDiscount(method, offer)
        else:
            # When returning a tax exclusive discount, it is assumed
            # that this will be used to calculate taxes which will then
            # be assigned directly to the method instance.
            return TaxExclusiveOfferDiscount(method, offer)
