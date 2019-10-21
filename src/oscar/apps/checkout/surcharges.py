from decimal import Decimal as D

from oscar.core import prices


class Base(object):
    """
    Surcharge interface class

    This is the superclass to the classes in surcharges.py. This allows using all
    surcharges interchangeably (aka polymorphism).

    The interface is all properties.
    """

    def __init__(self, excl_tax=None, incl_tax=None):
        self.excl_tax = excl_tax
        self.incl_tax = incl_tax

    def calculate(self, basket, **kwargs):
        raise NotImplementedError


class PercentageCharge(Base):
    name = "Percentage surcharge"

    def calculate(self, basket, **kwargs):
        if basket.total_excl_tax:
            return prices.Price(
                currency=basket.currency,
                excl_tax=basket.total_excl_tax * self.excl_tax / 100,
                incl_tax=basket.total_incl_tax * self.incl_tax / 100
            )
        else:
            return prices.Price(
                currency=basket.currency,
                excl_tax=D('0.0'),
                incl_tax=D('0.0')
            )


class FlatCharge(Base):
    name = "Flat surcharge"

    def calculate(self, basket, **kwargs):
        return prices.Price(
            currency=basket.currency,
            excl_tax=self.excl_tax,
            incl_tax=self.incl_tax)
