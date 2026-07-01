from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.partner import prices
from oscar.core.prices import TaxNotKnown


class TestUnavailable(TestCase):
    def setUp(self):
        self.price = prices.Unavailable()

    def test_means_unknown_tax(self):
        self.assertFalse(self.price.is_tax_known)

    def test_means_prices_dont_exist(self):
        self.assertFalse(self.price.exists)

    def test_means_price_attributes_are_none(self):
        self.assertIsNone(self.price.incl_tax)
        self.assertIsNone(self.price.excl_tax)
        self.assertIsNone(self.price.tax)


class TestFixedPriceWithoutTax(TestCase):
    def setUp(self):
        self.price = prices.FixedPrice("GBP", D("9.15"))

    def test_means_unknown_tax(self):
        self.assertFalse(self.price.is_tax_known)

    def test_has_correct_price(self):
        self.assertEqual(D("9.15"), self.price.excl_tax)

    # pylint: disable=pointless-statement
    def test_raises_exception_when_asking_for_price_incl_tax(self):
        with self.assertRaises(TaxNotKnown):
            self.price.incl_tax
