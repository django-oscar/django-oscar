from decimal import Decimal as D

from django.test import TestCase
import mock

from oscar.apps.checkout import calculators
from oscar.apps.shipping import methods
from oscar.core import prices


class TestOrderTotalCalculator(TestCase):

    def setUp(self):
        self.calculator = calculators.OrderTotalCalculator()

    def test_returns_correct_totals_when_tax_is_not_known(self):
        basket = mock.Mock()
        basket.total_excl_tax = D('10.00')
        basket.is_tax_known = False
        method = methods.FixedPrice(D('5.00'))

        total = self.calculator.calculate(basket, method)

        self.assertIsInstance(total, prices.Price)
        self.assertEqual(D('10.00') + D('5.00'), total.excl_tax)
        self.assertFalse(total.is_tax_known)
        with self.assertRaises(AttributeError):
            total.incl_tax
        with self.assertRaises(AttributeError):
            total.tax

    def test_returns_correct_totals_when_tax_is_known(self):
        basket = mock.Mock()
        basket.total_excl_tax = D('10.00')
        basket.total_incl_tax = D('12.00')
        basket.is_tax_known = True
        method = methods.FixedPrice(D('5.00'), D('5.50'))

        total = self.calculator.calculate(basket, method)

        self.assertIsInstance(total, prices.Price)
        self.assertEqual(D('10.00') + D('5.00'), total.excl_tax)
        self.assertTrue(total.is_tax_known)
        self.assertEqual(D('12.00') + D('5.50'), total.incl_tax)
        self.assertEqual(D('2.00') + D('0.50'), total.tax)
