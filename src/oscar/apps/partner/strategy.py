from collections import namedtuple
from decimal import Decimal as D

from oscar.core.compat import user_is_authenticated
from oscar.core.loading import get_class

Unavailable = get_class('partner.availability', 'Unavailable')
Available = get_class('partner.availability', 'Available')
StockRequiredAvailability = get_class('partner.availability', 'StockRequired')
UnavailablePrice = get_class('partner.prices', 'Unavailable')
FixedPrice = get_class('partner.prices', 'FixedPrice')
TaxInclusiveFixedPrice = get_class('partner.prices', 'TaxInclusiveFixedPrice')

# A container for policies
PurchaseInfo = namedtuple(
    'PurchaseInfo', ['price', 'availability', 'stockrecord'])


class Selector(object):
    """
    Responsible for returning the appropriate strategy class for a given
    user/session.

    This can be called in three ways:

    #) Passing a request and user.  This is for determining
       prices/availability for a normal user browsing the site.

    #) Passing just the user.  This is for offline processes that don't
       have a request instance but do know which user to determine prices for.

    #) Passing nothing.  This is for offline processes that don't
       correspond to a specific user.  Eg, determining a price to store in
       a search index.

    """

    def strategy(self, request=None, user=None, **kwargs):
        """
        Return an instanticated strategy instance
        """
        # Default to the backwards-compatible strategy of picking the first
        # stockrecord but charging zero tax.
        return Default(request)


class Base(object):
    """
    The base strategy class

    Given a product, strategies are responsible for returning a
    ``PurchaseInfo`` instance which contains:

    - The appropriate stockrecord for this customer
    - A pricing policy instance
    - An availability policy instance
    """

    def __init__(self, request=None):
        self.request = request
        self.user = None
        if request and user_is_authenticated(request.user):
            self.user = request.user

    def fetch_for_product(self, product, stockrecord=None):
        """
        Given a product, return a ``PurchaseInfo`` instance.

        The ``PurchaseInfo`` class is a named tuple with attributes:

        - ``price``: a pricing policy object.
        - ``availability``: an availability policy object.
        - ``stockrecord``: the stockrecord that is being used

        If a stockrecord is passed, return the appropriate ``PurchaseInfo``
        instance for that product and stockrecord is returned.
        """
        raise NotImplementedError(
            "A strategy class must define a fetch_for_product method "
            "for returning the availability and pricing "
            "information."
        )

    def fetch_for_parent(self, product):
        """
        Given a parent product, fetch a ``StockInfo`` instance
        """
        raise NotImplementedError(
            "A strategy class must define a fetch_for_parent method "
            "for returning the availability and pricing "
            "information."
        )

    def fetch_for_line(self, line, stockrecord=None):
        """
        Given a basket line instance, fetch a ``PurchaseInfo`` instance.

        This method is provided to allow purchase info to be determined using a
        basket line's attributes.  For instance, "bundle" products often use
        basket line attributes to store SKUs of contained products.  For such
        products, we need to look at the availability of each contained product
        to determine overall availability.
        """
        # Default to ignoring any basket line options as we don't know what to
        # do with them within Oscar - that's up to your project to implement.
        return self.fetch_for_product(line.product)


class Structured(Base):
    """
    A strategy class which provides separate, overridable methods for
    determining the 3 things that a ``PurchaseInfo`` instance requires:

    #) A stockrecord
    #) A pricing policy
    #) An availability policy
    """

    def fetch_for_product(self, product, stockrecord=None):
        """
        Return the appropriate ``PurchaseInfo`` instance.

        This method is not intended to be overridden.
        """
        if stockrecord is None:
            stockrecord = self.select_stockrecord(product)
        return PurchaseInfo(
            price=self.pricing_policy(product, stockrecord),
            availability=self.availability_policy(product, stockrecord),
            stockrecord=stockrecord)

    def fetch_for_parent(self, product):
        # Select children and associated stockrecords
        children_stock = self.select_children_stockrecords(product)
        return PurchaseInfo(
            price=self.parent_pricing_policy(product, children_stock),
            availability=self.parent_availability_policy(
                product, children_stock),
            stockrecord=None)

    def select_stockrecord(self, product):
        """
        Select the appropriate stockrecord
        """
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'select_stockrecord' method")

    def select_children_stockrecords(self, product):
        """
        Select appropriate stock record for all children of a product
        """
        records = []
        for child in product.children.all():
            # Use tuples of (child product, stockrecord)
            records.append((child, self.select_stockrecord(child)))
        return records

    def pricing_policy(self, product, stockrecord):
        """
        Return the appropriate pricing policy
        """
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'pricing_policy' method")

    def parent_pricing_policy(self, product, children_stock):
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'parent_pricing_policy' method")

    def availability_policy(self, product, stockrecord):
        """
        Return the appropriate availability policy
        """
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'availability_policy' method")

    def parent_availability_policy(self, product, children_stock):
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'parent_availability_policy' method")


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
            return Unavailable()
        if not product.get_product_class().track_stock:
            return Available()
        else:
            return StockRequiredAvailability(
                stockrecord.net_stock_level)

    def parent_availability_policy(self, product, children_stock):
        # A parent product is available if one of its children is
        for child, stockrecord in children_stock:
            policy = self.availability_policy(product, stockrecord)
            if policy.is_available_to_buy:
                return Available()
        return Unavailable()


class NoTax(object):
    """
    Pricing policy mixin for use with the ``Structured`` base strategy.
    This mixin specifies zero tax and uses the ``price_excl_tax`` from the
    stockrecord.
    """

    def pricing_policy(self, product, stockrecord):
        # Check stockrecord has the appropriate data
        if not stockrecord or stockrecord.price_excl_tax is None:
            return UnavailablePrice()
        return FixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax,
            tax=D('0.00'))

    def parent_pricing_policy(self, product, children_stock):
        stockrecords = [x[1] for x in children_stock if x[1] is not None]
        if not stockrecords:
            return UnavailablePrice()
        # We take price from first record
        stockrecord = stockrecords[0]
        return FixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax,
            tax=D('0.00'))


class FixedRateTax(object):
    """
    Pricing policy mixin for use with the ``Structured`` base strategy.  This
    mixin applies a fixed rate tax to the base price from the product's
    stockrecord.  The price_incl_tax is quantized to two decimal places.
    Rounding behaviour is Decimal's default
    """
    rate = D('0')  # Subclass and specify the correct rate
    exponent = D('0.01')  # Default to two decimal places

    def pricing_policy(self, product, stockrecord):
        if not stockrecord:
            return UnavailablePrice()
        rate = self.get_rate(product, stockrecord)
        exponent = self.get_exponent(stockrecord)
        tax = (stockrecord.price_excl_tax * rate).quantize(exponent)
        return TaxInclusiveFixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax,
            tax=tax)

    def parent_pricing_policy(self, product, children_stock):
        stockrecords = [x[1] for x in children_stock if x[1] is not None]
        if not stockrecords:
            return UnavailablePrice()

        # We take price from first record
        stockrecord = stockrecords[0]
        rate = self.get_rate(product, stockrecord)
        exponent = self.get_exponent(stockrecord)
        tax = (stockrecord.price_excl_tax * rate).quantize(exponent)

        return FixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax,
            tax=tax)

    def get_rate(self, product, stockrecord):
        """
        This method serves as hook to be able to plug in support for varying tax rates
        based on the product.

        TODO: Needs tests.
        """
        return self.rate

    def get_exponent(self, stockrecord):
        """
        This method serves as hook to be able to plug in support for a varying exponent
        based on the currency.

        TODO: Needs tests.
        """
        return self.exponent


class DeferredTax(object):
    """
    Pricing policy mixin for use with the ``Structured`` base strategy.
    This mixin does not specify the product tax and is suitable to territories
    where tax isn't known until late in the checkout process.
    """

    def pricing_policy(self, product, stockrecord):
        if not stockrecord:
            return UnavailablePrice()
        return FixedPrice(
            currency=stockrecord.price_currency,
            excl_tax=stockrecord.price_excl_tax)

    def parent_pricing_policy(self, product, children_stock):
        stockrecords = [x[1] for x in children_stock if x[1] is not None]
        if not stockrecords:
            return UnavailablePrice()

        # We take price from first record
        stockrecord = stockrecords[0]

        return FixedPrice(
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


class UK(UseFirstStockRecord, StockRequired, FixedRateTax, Structured):
    """
    Sample strategy for the UK that:

    - uses the first stockrecord for each product (effectively assuming
        there is only one).
    - requires that a product has stock available to be bought
    - applies a fixed rate of tax on all products

    This is just a sample strategy used for internal development.  It is not
    recommended to be used in production, especially as the tax rate is
    hard-coded.
    """
    # Use UK VAT rate (as of December 2013)
    rate = D('0.20')


class US(UseFirstStockRecord, StockRequired, DeferredTax, Structured):
    """
    Sample strategy for the US.

    - uses the first stockrecord for each product (effectively assuming
      there is only one).
    - requires that a product has stock available to be bought
    - doesn't apply a tax to product prices (normally this will be done
      after the shipping address is entered).

    This is just a sample one used for internal development.  It is not
    recommended to be used in production.
    """
