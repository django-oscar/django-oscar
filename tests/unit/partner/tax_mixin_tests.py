from decimal import Decimal as D

from django.test import TestCase
import mock

from oscar.apps.partner import strategy
from oscar.core import prices


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

    def test_doesnt_return_tax(self):
        policy = self.mixin.pricing_policy(
            self.product, self.stockrecord)
        with self.assertRaises(prices.TaxNotKnown):
            policy.get_unit_price().tax

    def test_doesnt_have_tax_inclusive_price(self):
        policy = self.mixin.pricing_policy(
            self.product, self.stockrecord)
        with self.assertRaises(prices.TaxNotKnown):
            policy.get_unit_price().incl_tax


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
        self.assertEqual(self.mixin.rate * self.stockrecord.price_excl_tax,
                         policy.get_unit_price().tax)

    def test_adds_tax_to_net_price(self):
        policy = self.mixin.pricing_policy(
            self.product, self.stockrecord)
        self.assertEqual(D('13.20'), policy.get_unit_price().incl_tax)
