from django.test import TestCase
from decimal import Decimal as D

from oscar.core.prices import TaxNotKnown
from oscar.apps.partner import prices


class TestUnavailable(TestCase):

    def setUp(self):
        self.pricing_policy = prices.Unavailable()
        self.price = self.pricing_policy.get_unit_price()

    def test_means_unknown_tax(self):
        self.assertFalse(self.price.is_tax_known)

    def test_means_prices_dont_exist(self):
        self.assertFalse(self.pricing_policy.exists)
        self.assertIsNone(self.price.excl_tax)

    def test_means_tax_cant_be_accessed(self):
        self.assertRaises(TaxNotKnown, getattr, self.price, 'incl_tax')
        self.assertRaises(TaxNotKnown, getattr, self.price, 'tax')


class TestFixedPriceWithoutTax(TestCase):

    def setUp(self):
        self.pricing_policy = prices.FixedPrice('GBP', D('9.15'))
        self.price = self.pricing_policy.get_unit_price()

    def test_means_unknown_tax(self):
        self.assertFalse(self.price.is_tax_known)

    def test_has_correct_price(self):
        self.assertEqual(D('9.15'), self.price.excl_tax)

    def test_raises_exception_when_asking_for_price_incl_tax(self):
        with self.assertRaises(TaxNotKnown):
            self.price.incl_tax
