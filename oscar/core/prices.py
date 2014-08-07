class TaxNotKnown(Exception):
    """
    Exception for when a tax-inclusive price is requested but we don't know
    what the tax applicable is (yet).
    """


class Price(object):
    """
    Simple price class that encapsulates a price and its tax information

    Attributes:
        incl_tax (Decimal): Price including taxes
        excl_tax (Decimal): Price excluding taxes
        tax (Decimal): Tax amount
        is_tax_known (bool): Whether tax is known
        currency (str): 3 character currency code
    """

    def __init__(self, currency, excl_tax, incl_tax=None, tax=None):
        self.currency = currency
        self.excl_tax = excl_tax
        if incl_tax is not None:
            self.incl_tax = incl_tax
            self.is_tax_known = True
        elif tax is not None:
            self.incl_tax = excl_tax + tax
            self.is_tax_known = True
        else:
            self.incl_tax = None
            self.is_tax_known = False

    def _get_tax(self):
        return self.incl_tax - self.excl_tax

    def _set_tax(self, value):
        self.incl_tax = self.excl_tax + value
        self.is_tax_known = True

    tax = property(_get_tax, _set_tax)

    def __repr__(self):
        if self.is_tax_known:
            return "%s(currency=%r, excl_tax=%r, incl_tax=%r, tax=%r)" % (
                self.__class__.__name__, self.currency, self.excl_tax,
                self.incl_tax, self.tax)
        return "%s(currency=%r, excl_tax=%r)" % (
            self.__class__.__name__, self.currency, self.excl_tax)

    def __eq__(self, other):
        """
        Two price objects are equal if currency, price.excl_tax and tax match.
        """
        return (self.currency == other.currency and
                self.excl_tax == other.excl_tax and
                self.incl_tax == other.incl_tax)
