from decimal import Decimal as D

from oscar.core import prices


class Base(object):
    """
    Surcharge interface class

    This is the superclass to the classes in surcharges.py. This allows using all
    surcharges interchangeably (aka polymorphism).

    The interface is all properties.
    """

    # The name of the surcharge, shown to the customer during checkout
    name = "Default surcharge"

    excl_tax = None
    incl_tax = None

    def __init__(self, excl_tax=None, incl_tax=None):
        if excl_tax is not None:
            self.excl_tax = excl_tax
        if incl_tax is not None:
            self.incl_tax = incl_tax


class PercentageCharge(Base):
    name = "Percentage surcharge"

    def calculate(self, basket):
        if basket.total_excl_tax:
            return prices.Price(
                currency=basket.currency,
                excl_tax=basket.total_excl_tax * (self.excl_tax / 100),
                incl_tax=basket.total_incl_tax * (self.incl_tax / 100)
            )
        else:
            return prices.Price(
                currency=basket.currency,
                excl_tax=D('0.0'),
                incl_tax=D('0.0')
            )


class FlatCharge(Base):
    name = "Flat surcharge"

    def calculate(self, basket):
        return prices.Price(
            currency=basket.currency,
            excl_tax=self.excl_tax,
            incl_tax=self.incl_tax)
