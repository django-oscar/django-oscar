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
            self.tax = incl_tax - excl_tax
        elif tax is not None:
            self.incl_tax = excl_tax + tax
            self.is_tax_known = True
            self.tax = tax
        else:
            self.is_tax_known = False
