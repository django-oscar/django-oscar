from collections import namedtuple
from decimal import Decimal as D

from . import availability, prices


# A container for policies
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
        a search index.
    """

    def strategy(self, request=None, user=None, **kwargs):
        """
        Return an instanticated strategy instance
        """
        # Default to the backwards-compatible strategy of picking the first
        # stockrecord.
        return Default(request)
        #return US(request)


class Base(object):
    """
    The base strategy class

    Given a product, strategies are responsible for returning a ``StockInfo``
    instance which contains:

    - The appropriate stockrecord for this customer
    - A pricing policy instance
    - An availability policy instance
    """

    def __init__(self, request=None):
        self.request = request
        self.user = None
        if request and request.user.is_authenticated():
            self.user = request.user

    def fetch(self, product, stockrecord=None):
        """
        Given a product, return a ``StockInfo`` instance.

        The ``StockInfo`` class is a named tuple with attributes:

        - ``price``: a pricing policy object.
        - ``availability``: an availability policy object.
        - ``stockrecord``: the stockrecord that is being used to calculate prices and

        If a stockrecord is passed, return the appropriate ``StockInfo``
        instance for that product and stockrecord is returned.
        """
        raise NotImplementedError(
            "A strategy class must define a fetch method "
            "for returning the availability and pricing "
            "information."
        )


class Structured(Base):
    """
    A strategy class which provides separate, overridable methods for
    determining the 3 things that a ``StockInfo`` instance requires:

    #) A stockrecord
    #) A pricing policy
    #) An availability policy
    """

    def fetch(self, product, stockrecord=None):
        """
        Return the appropriate stockinfo instance.

        This method is not intended to be overridden.
        """
        if stockrecord is None:
            stockrecord = self.select_stockrecord(product)
        return StockInfo(
            price=self.pricing_policy(product, stockrecord),
            availability=self.availability_policy(product, stockrecord),
            stockrecord=stockrecord)

    def select_stockrecord(self, product):
        """
        Select the appropriate stockrecord
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
    Stockrecord selection mixin for use with the ``Structured`` base strategy.
    This mixin picks the first (normally only) stockrecord to fulfil a product.

    This is backwards compatible with Oscar<0.6 where only one stockrecord per
    product was permitted.
    """

    def select_stockrecord(self, product):
        try:
            return product.stockrecords.all()[0]
        except IndexError:
            return None


class StockRequired(object):
    """
    Availability policy mixin for use with the ``Structured`` base strategy.
    This mixin ensures that a product can only be bought if it has stock
    available (if stock is being tracked).
    """

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
    Pricing policy mixin for use with the ``Structured`` base strategy.
    This mixin specifies zero tax and uses the ``price_excl_tax`` from the
    stockrecord.
    """

    def pricing_policy(self, product, stockrecord):
        if not stockrecord:
            return prices.Unavailable()
        return prices.FixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax,
            tax=D('0.00'))


class FixedRateTax(object):
    """
    Pricing policy mixin for use with the ``Structured`` base strategy.
    This mixin applies a fixed rate tax to the base price from the product's
    stockrecord.
    """
    rate = D('0.20')

    def pricing_policy(self, product, stockrecord):
        if not stockrecord:
            return prices.Unavailable()
        return prices.FixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax,
            tax=stockrecord.price_excl_tax * self.rate)


class DeferredTax(object):
    """
    Pricing policy mixin for use with the ``Structured`` base strategy.
    This mixin does not specify the product tax and is suitable to territories
    where tax isn't known until late in the checkout process.
    """

    def pricing_policy(self, product, stockrecord):
        if not stockrecord:
            return prices.Unavailable()
        return prices.FixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax)


# Example strategy composed of above mixins.  For real projects, it's likely
# you'll want to use a different pricing mixin as you'll probably want to
# charge tax!


class Default(UseFirstStockRecord, StockRequired, NoTax, Structured):
    """
    Default stock/price strategy that uses the first found stockrecord for a
    product, ensures that stock is available (unless the product class
    indicates that we don't need to track stock) and charges zero tax.
    """


class US(UseFirstStockRecord, StockRequired, DeferredTax, Structured):
    """
    Default strategy for the USA (just for testing really)
    """
