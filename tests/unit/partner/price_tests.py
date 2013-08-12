from django.test import TestCase
from decimal import Decimal as D

from oscar.apps.partner import prices, models


class TestNoStockRecord(TestCase):

    def setUp(self):
        self.price = prices.NoStockRecord()

    def test_means_unknown_tax(self):
        self.assertFalse(self.price.is_tax_known)

    def test_means_prices_dont_exist(self):
        self.assertFalse(self.price.exists)

    def test_means_price_attributes_are_none(self):
        self.assertIsNone(self.price.incl_tax)
        self.assertIsNone(self.price.excl_tax)
        self.assertIsNone(self.price.tax)


class TestWrappedStockRecord(TestCase):

    def setUp(self):
        self.record = models.StockRecord(
            price_excl_tax=D('12.99'))
        self.price = prices.WrappedStockRecord(self.record)

    def test_means_unknown_tax(self):
        self.assertFalse(self.price.is_tax_known)

    def test_has_correct_price(self):
        self.assertEquals(self.record.price_excl_tax,
                          self.price.excl_tax)
