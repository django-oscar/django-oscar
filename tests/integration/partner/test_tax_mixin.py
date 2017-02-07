from decimal import Decimal as D

from django.test import TestCase
import mock

from oscar.apps.partner import strategy


class TestNoTaxMixin(TestCase):

    def setUp(self):
        self.mixin = strategy.NoTax()
        self.product = mock.Mock()
        self.stockrecord = mock.Mock()
        self.stockrecord.price_excl_tax = D('12.00')

    def test_returns_no_prices_without_stockrecord(self):
        policy = self.mixin.pricing_policy(
            self.product, None)
        self.assertFalse(policy.exists)

    def test_returns_zero_tax(self):
        policy = self.mixin.pricing_policy(
            self.product, self.stockrecord)
        self.assertEqual(D('0.00'), policy.tax)

    def test_doesnt_add_tax_to_net_price(self):
        policy = self.mixin.pricing_policy(
            self.product, self.stockrecord)
        self.assertEqual(D('12.00'), policy.incl_tax)


class TestFixedRateTaxMixin(TestCase):

    def setUp(self):
        self.mixin = strategy.FixedRateTax()
        self.mixin.rate = D('0.10')
        self.product = mock.Mock()
        self.stockrecord = mock.Mock()
        self.stockrecord.price_excl_tax = D('12.00')

    def test_returns_no_prices_without_stockrecord(self):
        policy = self.mixin.pricing_policy(
            self.product, None)
        self.assertFalse(policy.exists)

    def test_returns_correct_tax(self):
        policy = self.mixin.pricing_policy(
            self.product, self.stockrecord)
        expected_tax = self.stockrecord.price_excl_tax * self.mixin.get_rate(
            self.product, self.stockrecord)
        self.assertEqual(expected_tax, policy.tax)

    def test_adds_tax_to_net_price(self):
        policy = self.mixin.pricing_policy(
            self.product, self.stockrecord)
        self.assertEqual(D('13.20'), policy.incl_tax)
