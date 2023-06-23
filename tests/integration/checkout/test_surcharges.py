from decimal import Decimal as D

from django.test import TestCase

from oscar.core import prices
from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.basket import add_product

SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")
PercentageCharge = get_class("checkout.surcharges", "PercentageCharge")
FlatCharge = get_class("checkout.surcharges", "FlatCharge")


class TestSurcharges(TestCase):
    def setUp(self):
        self.applicator = SurchargeApplicator()
        self.basket = factories.create_basket(empty=True)

    def test_stock_surcharges(self):
        add_product(self.basket, D("12.00"))
        surcharges = self.applicator.get_applicable_surcharges(self.basket)

        self.assertEqual(surcharges.total.excl_tax, D("20.0"))
        self.assertEqual(surcharges.total.incl_tax, D("22.0"))

    def test_percentage_surcharge(self):
        percentage_surcharge = PercentageCharge(percentage=D(10))
        add_product(self.basket, D(12))
        price = percentage_surcharge.calculate(self.basket)

        self.assertEqual(self.basket.total_incl_tax, D(12))
        self.assertEqual(price.incl_tax, D("1.20"))

    def test_percentage_empty_basket(self):
        percentage_surcharge = PercentageCharge(percentage=D(10))
        price = percentage_surcharge.calculate(self.basket)

        self.assertEqual(self.basket.total_incl_tax, D(0))
        self.assertEqual(price.incl_tax, D(0))

    def test_flat_surcharge(self):
        flat_surcharge = FlatCharge(excl_tax=D(1), incl_tax=D("1.21"))
        add_product(self.basket, D(12))
        price = flat_surcharge.calculate(self.basket)

        self.assertEqual(self.basket.total_incl_tax, D(12))
        self.assertEqual(price.incl_tax, D("1.21"))
        self.assertEqual(price.excl_tax, D(1))

    def test_percentage_with_shipping_charge(self):
        percentage_surcharge = PercentageCharge(percentage=D(4))
        add_product(self.basket, D(10))
        shipping_charge = prices.Price(
            currency=self.basket.currency, excl_tax=D("3.95"), tax=D("1.05")
        )
        price = percentage_surcharge.calculate(
            self.basket, shipping_charge=shipping_charge
        )

        self.assertEqual(self.basket.total_incl_tax, D(10))
        self.assertEqual(shipping_charge.incl_tax, D(5))
        self.assertEqual(price.incl_tax, D("0.6"))
