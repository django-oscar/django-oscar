import warnings
from decimal import Decimal as D


class WarningDecimal(D):
    """
    This is a helper class that is not used by default. Currently, non-linear
    prices don't work with offers, which should be addressed at some point.
    To easily spot places in the codebase where a price is multiplied
    (instead of using get_price()), replace the regular Decimal class with this
    in the Price class below.

    Aliasing to WD is recommended.
    """

    def __mul__(self, other, context=None):
        warnings.warn(
            "You are multiplying a price. You should use "
            "get_price(quantity) instead.", RuntimeWarning)
        return super(WarningDecimal, self).__mul__(other, context)

    __rmul__ = __mul__

    def quantize(self, *args, **kwargs):
        result = super(WarningDecimal, self).quantize(*args, **kwargs)
        return WarningDecimal(result)


class TaxNotKnown(Exception):
    """
    Exception for when a tax-inclusive price is requested but we don't know
    what the tax applicable is (yet).
    """
    pass


class Price(object):
    """
    This class encapsulates a price and its tax information.

    Amounts are returned as decimals internally and are quantized
    to the given exponent. If no exponent is given, it defaults to two digits
    after the comma.

    Attributes:
        excl_tax (Decimal): Price excluding taxes
        tax (Decimal): Tax amount, or None if tax is not known.
        incl_tax (Decimal): Price including taxes. None if tax is not known.
        is_tax_known (bool): Whether tax is known
        currency (str): 3 character currency code

    Price instances are intentionally read-only apart from setting and clearing
    tax.
    """

    def __init__(self, currency, excl_tax, incl_tax=None, tax=None,
                 exponent=None):
        self.currency = currency
        self.exponent = exponent or D('0.01')
        self._excl_tax = excl_tax
        if incl_tax is not None:
            self._incl_tax = incl_tax
        else:
            self.tax = tax

    @property
    def excl_tax(self):
        if self._excl_tax is not None:
            return D(self._excl_tax).quantize(self.exponent)

    @property
    def tax(self):
        if self.is_tax_known:
            return D(self.incl_tax - self.excl_tax).quantize(self.exponent)
        raise TaxNotKnown

    @tax.setter
    def tax(self, value):
        if value is None:
            self._incl_tax = None  # clears any tax
        elif self._excl_tax is None:
            raise ValueError("Can't set a tax for unset base price")
        else:
            self._incl_tax = self._excl_tax + value

    @property
    def incl_tax(self):
        if self.is_tax_known:
            return D(self._incl_tax).quantize(self.exponent)
        raise TaxNotKnown

    @property
    def is_tax_known(self):
        return self._excl_tax is not None and self._incl_tax is not None

    def __repr__(self):
        if self.is_tax_known:
            return "%s(currency=%r, excl_tax=%r, incl_tax=%r, tax=%r)" % (
                self.__class__.__name__, self.currency, self.excl_tax,
                self.incl_tax, self.tax)
        return "%s(currency=%r, excl_tax=%r)" % (
            self.__class__.__name__, self.currency, self.excl_tax)
