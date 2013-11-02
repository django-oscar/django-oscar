from oscar.core import prices


class Base(object):
    """
    The interface that any pricing policy must support
    """

    #: Whether any prices exist
    exists = False

    #: Whether tax is known
    is_tax_known = False

    #: Price excluding tax
    excl_tax = None

    #: Price including tax
    incl_tax = None

    #: Price tax
    tax = None

    #: Retail price
    retail = None

    #: Price currency (3 char code)
    currency = None


class Unavailable(Base):
    """
    This should be used as a pricing policy when a product is unavailable and
    no prices are known.
    """


class FixedPrice(Base):
    """
    This should be used for when the price of a product is known in advance.

    It can work for when tax isn't known (like in the US).
    """
    exists = True

    def __init__(self, currency, excl_tax, tax=None):
        self.currency = currency
        self.excl_tax = excl_tax
        self.tax = tax

    @property
    def incl_tax(self):
        if self.is_tax_known:
            return self.excl_tax + self.tax
        raise prices.TaxNotKnown(
            "Can't calculate price.incl_tax as tax isn't known")

    @property
    def is_tax_known(self):
        return self.tax is not None


class DelegateToStockRecord(Base):
    """
    Pricing policy which wraps around an existing stockrecord.

    This is backwards compatible with Oscar<0.6 where taxes were calculated by
    "partner wrappers" which wrapped around stockrecords.
    """
    is_tax_known = True

    def __init__(self, stockrecord):
        self.stockrecord = stockrecord

    @property
    def exists(self):
        return self.stockrecord is not None

    @property
    def excl_tax(self):
        return self.stockrecord.price_excl_tax

    @property
    def incl_tax(self):
        return self.stockrecord.price_incl_tax

    @property
    def tax(self):
        return self.stockrecord.price_tax

    @property
    def retail(self):
        return self.stockrecord.price_retail

    @property
    def currency(self):
        return self.stockrecord.price_currency
