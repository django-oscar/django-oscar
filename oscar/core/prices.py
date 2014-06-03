class TaxNotKnown(Exception):
    """
    Exception for when a tax-inclusive price is requested but we don't know
    what the tax applicable is (yet).
    """


class Price(object):
    """
    Simple price class that encapsulates a price and its tax information

    Attributes:
        incl_tax (Decimal): Price including taxes. None if tax is not known.
        excl_tax (Decimal): Price excluding taxes
        tax (Decimal): Tax amount, or None if tax is not known.
        is_tax_known (bool): Whether tax is known
        currency (str): 3 character currency code

    Price instances should be treated as read-only instances, as pricing
    policies are responsible for calculating tax and quantity pricing.
    """

    def __init__(self, currency, excl_tax, incl_tax=None, tax=None):
        self.currency = currency
        self.excl_tax = excl_tax
        if incl_tax is not None:
            self._incl_tax = incl_tax
            self.is_tax_known = True
        elif tax is not None:
            self._incl_tax = excl_tax + tax
            self.is_tax_known = True
        else:
            self.is_tax_known = False

    @property
    def tax(self):
        if self.is_tax_known:
            return self.incl_tax - self.excl_tax
        raise TaxNotKnown

    @property
    def incl_tax(self):
        if self.is_tax_known:
            return self._incl_tax
        raise TaxNotKnown

    def __repr__(self):
        if self.is_tax_known:
            return "%s(currency=%r, excl_tax=%r, incl_tax=%r, tax=%r)" % (
                self.__class__.__name__, self.currency, self.excl_tax,
                self.incl_tax, self.tax)
        return "%s(currency=%r, excl_tax=%r)" % (
            self.__class__.__name__, self.currency, self.excl_tax)
