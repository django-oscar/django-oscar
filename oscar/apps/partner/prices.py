import warnings

from oscar.core import prices


class Base(object):
    """
    The interface that any pricing policy must support
    """

    #: Whether any prices exist
    exists = False

    #: Whether tax is known
    is_tax_known = False

    #: Price currency (3 char code)
    currency = None

    #: Price for single unit to use for offer calculations
    #: Note that offers app currently won't work with non-linear prices!
    @property
    def effective_price(self):
        # Default to using the price excluding tax for calculations
        return self.get_price().excl_tax

    def get_price(self, quantity=1):
        """
        Returns a oscar.core.prices.Price instance for a given quantity.
        """
        return prices.Price(currency=None, excl_tax=None)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

    # -- Deprecated attributes -- #

    #: Price for single unit excluding tax
    @property
    def excl_tax(self):
        warnings.warn(
            "The excl_tax property is deprecated. "
            "Use get_price(qty).excl_tax instead.", DeprecationWarning)
        return self.get_price().excl_tax

    #: Price for single unit including tax
    @property
    def incl_tax(self):
        warnings.warn(
            "The incl_tax property is deprecated. "
            "Use get_price(qty).incl_tax instead.", DeprecationWarning)
        return self.get_price().incl_tax

    #: Price tax for single unit
    @property
    def tax(self):
        warnings.warn(
            "The tax property is deprecated. "
            "Use get_price(qty).tax instead.", DeprecationWarning)
        return self.get_price().tax


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

    def __init__(self, currency, excl_tax, tax_rate=None):
        self.currency = currency
        self._excl_tax = excl_tax
        self.tax_rate = tax_rate

    def calculate_total(self, quantity):
        """
        Implements a naive linear pricing. Override this function to implement
        e.g. bulk pricing.
        Defaults to quantizing with the same precision as the unit price.
        """
        return self._excl_tax * quantity

    def calculate_tax(self, total_excl_tax):
        """
        Calculates tax, given a non-tax total.
        Defaults to quantizing with the same precision as the given total,
        which should be the precision of the prices.
        """
        if self.tax_rate is None:
            return None
        return total_excl_tax * self.tax_rate

    def get_price(self, quantity=1):
        total_excl_tax = self.calculate_total(quantity)
        tax = self.calculate_tax(total_excl_tax)
        return prices.Price(self.currency, total_excl_tax, tax=tax)

    @property
    def is_tax_known(self):
        return self.tax_rate is not None


class TaxInclusiveFixedPrice(FixedPrice):
    """
    Specialised version of FixedPrice that must have tax passed.  It also
    specifies that offers should use the tax-inclusive price (which is the norm
    in the UK).
    """
    exists = is_tax_known = True

    def __init__(self, currency, excl_tax, tax_rate):
        if tax_rate is None:
            raise ValueError("You must specify a tax rate for "
                             "TaxInclusiveFixedPrice. It may be zero.")
        super(TaxInclusiveFixedPrice, self).__init__(
            currency, excl_tax, tax_rate)

    @property
    def effective_price(self):
        return self.get_price().incl_tax
