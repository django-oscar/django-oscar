from decimal import Decimal as D
from unittest import mock

from django.test import TestCase

from oscar.apps.checkout import calculators
from oscar.core import prices
from oscar.core.loading import get_class

SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")


class TestOrderTotalCalculator(TestCase):
    def setUp(self):
        self.calculator = calculators.OrderTotalCalculator()

    def test_returns_correct_totals_when_tax_is_not_known(self):
        basket = mock.Mock()
        basket.total_excl_tax = D("10.00")
        basket.is_tax_known = False

        shipping_charge = prices.Price(currency=basket.currency, excl_tax=D("5.00"))

        applicator = SurchargeApplicator()
        surcharges = applicator.get_applicable_surcharges(basket)

        total = self.calculator.calculate(basket, shipping_charge, surcharges)

        self.assertIsInstance(total, prices.Price)
        self.assertEqual(D("10.00") + D("5.00") + D("10.0"), total.excl_tax)
        self.assertFalse(total.is_tax_known)

    def test_returns_correct_totals_when_tax_is_known(self):
        basket = mock.Mock()
        basket.total_excl_tax = D("10.00")
        basket.total_incl_tax = D("12.00")
        basket.is_tax_known = True

        shipping_charge = prices.Price(
            currency=basket.currency, excl_tax=D("5.00"), tax=D("0.50")
        )

        applicator = SurchargeApplicator()
        surcharges = applicator.get_applicable_surcharges(basket)

        total = self.calculator.calculate(basket, shipping_charge, surcharges)

        self.assertIsInstance(total, prices.Price)
        self.assertEqual(D("10.00") + D("5.00") + D("20.0"), total.excl_tax)
        self.assertTrue(total.is_tax_known)
        self.assertEqual(D("12.00") + D("5.50") + D("22.00"), total.incl_tax)
        self.assertEqual(D("2.00") + D("0.50") + D("2.00"), total.tax)
