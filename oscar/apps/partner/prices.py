class TaxNotKnown(Exception):
    """
    Exception for when a tax-inclusive price is requested but we don't know
    what the tax applicable is (yet).
    """


class Base(object):
    """
    The interface that any pricing policy must support
    """

    #: Whether any prices exist
    exists = False

    #: Whether tax is known
    is_tax_known = False

    #: Normal price properties
    excl_tax = incl_tax = tax = None

    #: Currency prices are in
    currency = None


class Unavailable(Base):
    """
    No stockrecord, therefore no prices
    """


class FixedPrice(Base):
    exists = True

    def __init__(self, excl_tax, tax=None):
        self.excl_tax = excl_tax
        self.tax = tax

    @property
    def incl_tax(self):
        if self.is_tax_known:
            return self.excl_tax + self.tax
        raise TaxNotKnown("Can't calculate price.incl_tax as tax isn't known")

    @property
    def is_tax_known(self):
        return self.tax is not None


class DelegateToStockRecord(Base):
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
    def currency(self):
        return self.stockrecord.price_currency
