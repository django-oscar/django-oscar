from decimal import Decimal as D

from django.utils.translation import gettext_lazy as _

from oscar.core import prices


class BaseSurcharge:
    """
    Surcharge interface class

    This is the superclass to the classes in surcharges.py. This allows using all
    surcharges interchangeably (aka polymorphism).

    The interface is all properties.
    """

    def calculate(self, basket, **kwargs):
        raise NotImplementedError


class PercentageCharge(BaseSurcharge):
    name = _("Percentage surcharge")
    code = "percentage-surcharge"

    def __init__(self, percentage):
        self.percentage = percentage

    def calculate(self, basket, **kwargs):
        if not basket.is_empty:
            shipping_charge = kwargs.get("shipping_charge")

            if shipping_charge is not None:
                total_excl_tax = basket.total_excl_tax + shipping_charge.excl_tax
                total_incl_tax = basket.total_incl_tax + shipping_charge.incl_tax
            else:
                total_excl_tax = basket.total_excl_tax
                total_incl_tax = basket.total_incl_tax

            return prices.Price(
                currency=basket.currency,
                excl_tax=total_excl_tax * self.percentage / 100,
                incl_tax=total_incl_tax * self.percentage / 100,
            )
        else:
            return prices.Price(
                currency=basket.currency, excl_tax=D("0.0"), incl_tax=D("0.0")
            )


class FlatCharge(BaseSurcharge):
    name = _("Flat surcharge")
    code = "flat-surcharge"

    def __init__(self, excl_tax=None, incl_tax=None):
        self.excl_tax = excl_tax
        self.incl_tax = incl_tax

    def calculate(self, basket, **kwargs):
        return prices.Price(
            currency=basket.currency, excl_tax=self.excl_tax, incl_tax=self.incl_tax
        )
