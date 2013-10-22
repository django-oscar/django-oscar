class TaxNotKnown(Exception):
    """
    Exception for when a tax-inclusive price is requested but we don't know
    what the tax applicable is (yet).
    """


class Price(object):
    is_tax_known = False

    def __init__(self, currency, excl_tax, incl_tax=None, tax=None):
        """
        You can either pass the price including tax or simply the tax
        """
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
