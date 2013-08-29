from collections import namedtuple
from decimal import Decimal as D

from . import availability, prices


StockInfo = namedtuple('StockInfo', ['price', 'availability', 'stockrecord'])


class Selector(object):
    """
    Responsible for returning the appropriate strategy class for a given
    user/session.

    This can be called in three ways:

        1. Passing a request and user.  This is for determining
        prices/availability for a normal user browsing the site.

        2. Passing just the user.  This is for offline processes that don't
        have a request instance but do know which user to determine prices for.

        3. Passing nothing.  This is for offline processes that don't
        correspond to a specific user.  Eg, determining a price to store in
        Solr's index.
    """
    def strategy(self, request=None, user=None, **kwargs):
        # Default to the backwards-compatible strategy of picking the first
        # stockrecord.
        return Default(request)


class Base(object):
    """
    Responsible for picking the appropriate pricing and availability wrappers
    for a product
    """

    def __init__(self, request=None):
        self.request = request
        self.user = None
        if request and request.user.is_authenticated():
            self.user = request.user

    def fetch(self, product, stockrecord=None):
        raise NotImplementedError(
            "A strategy class must define a fetch method "
            "for returning the availability and pricing "
            "information."
        )


class Structured(Base):

    def fetch(self, product, stockrecord=None):
        if stockrecord is None:
            stockrecord = self.select_stockrecord(product)
        return StockInfo(
            price=self.pricing_policy(product, stockrecord),
            availability=self.availability_policy(product, stockrecord),
            stockrecord=stockrecord)

    def select_stockrecord(self, product):
        """
        Select the appropriate stockrecord to go with the passed product
        """
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'select_stockrecord' method")

    def pricing_policy(self, product, stockrecord):
        """
        Return the appropriate pricing policy
        """
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'pricing_policy' method")

    def availability_policy(self, product, stockrecord):
        """
        Return the appropriate availability policy
        """
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'availability_policy' method")


# Mixins - these can be used to construct the appropriate strategy class


class UseFirstStockRecord(object):
    """
    Always use the first (normally only) stock record for a product
    """

    def select_stockrecord(self, product):
        try:
            return product.stockrecords.all()[0]
        except IndexError:
            return None


class StockRequired(object):

    def availability_policy(self, product, stockrecord):
        if not stockrecord:
            return availability.Unavailable()
        if not product.get_product_class().track_stock:
            return availability.Available()
        else:
            return availability.StockRequired(
                stockrecord.net_stock_level)


class NoTax(object):
    """
    Prices are the same as the price_excl_tax field on the
    stockrecord with zero tax.
    """

    def pricing_policy(self, product, stockrecord):
        if not stockrecord:
            return prices.Unavailable()
        return prices.FixedPrice(
            excl_tax=stockrecord.price_excl_tax,
            tax=D('0.00'))


class FixedRateTax(object):
    """
    Prices are the same as the price_excl_tax field on the
    stockrecord with zero tax.
    """
    rate = D('0.20')

    def pricing_policy(self, product, stockrecord):
        if not stockrecord:
            return prices.Unavailable()
        return prices.FixedPrice(
            excl_tax=stockrecord.price_excl_tax,
            tax=stockrecord.price_excl_tax * self.rate)


# Example strategy composed of above mixins.  For real projects, it's likely
# you'll want to use a different pricing mixin as you'll probably want to
# charge tax!


class Default(UseFirstStockRecord, StockRequired, NoTax, Structured):
    """
    Default stock/price strategy that uses the first found stockrecord for a
    product, ensures that stock is available (unless the product class
    indicates that we don't need to track stock) and charges zero tax.
    """
