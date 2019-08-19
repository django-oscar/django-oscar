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

    #: Price to use for offer calculations
    @property
    def effective_price(self):
        # Default to using the price excluding tax for calculations
        return self.excl_tax

    #: Price tax
    tax = None

    #: Retail price
    retail = None

    #: Price currency (3 char code)
    currency = None

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class Unavailable(Base):
    """
    This should be used as a pricing policy when a product is unavailable and
    no prices are known.
    """


class FixedPrice(Base):
    """
    This should be used for when the price of a product is known in advance.

    It can work for when tax isn't known (like in the US).

    Note that this price class uses the tax-exclusive price for offers, even if
    the tax is known.  This may not be what you want.  Use the
    TaxInclusiveFixedPrice class if you want offers to use tax-inclusive
    prices.
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
    def is_tax_known(self) -> bool:
        """
        Test whether the tax is known or not
        """
        return self.tax is not None


class TaxInclusiveFixedPrice(FixedPrice):
    """
    Specialised version of FixedPrice that must have tax passed.  It also
    specifies that offers should use the tax-inclusive price (which is the norm
    in the UK).
    """
    exists = is_tax_known = True

    def __init__(self, currency, excl_tax, tax):
        self.currency = currency
        self.excl_tax = excl_tax
        self.tax = tax

    @property
    def incl_tax(self):
        return self.excl_tax + self.tax

    @property
    def effective_price(self):
        return self.incl_tax
