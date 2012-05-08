from django.test import TestCase

from oscar.apps.partner.wrappers import DefaultWrapper
from oscar.apps.partner.models import StockRecord
from oscar.test.helpers import create_product


class DefaultWrapperTests(TestCase):

    def setUp(self):
        self.wrapper = DefaultWrapper()
        self.product = create_product()

    def test_num_in_stock_is_none_is_available_to_buy(self):
        record = StockRecord(num_in_stock=None)
        self.assertTrue(self.wrapper.is_available_to_buy(record))

    def test_zero_stock_is_not_available_to_buy(self):
        record = StockRecord(num_in_stock=0)
        self.assertFalse(self.wrapper.is_available_to_buy(record))

    def test_nonzero_stock_is_available_to_buy(self):
        record = StockRecord(num_in_stock=10)
        self.assertTrue(self.wrapper.is_available_to_buy(record))

    def test_matching_purchase_is_permitted(self):
        record = StockRecord(num_in_stock=4, product=self.product)
        result, reason = self.wrapper.is_purchase_permitted(record, quantity=4)
        self.assertTrue(result)

    def test_smaller_purchase_is_permitted(self):
        record = StockRecord(num_in_stock=4, product=self.product)
        result, reason = self.wrapper.is_purchase_permitted(record, quantity=3)
        self.assertTrue(result)

    def test_too_large_purchase_is_not_permitted(self):
        record = StockRecord(num_in_stock=4, product=self.product)
        result, reason = self.wrapper.is_purchase_permitted(record, quantity=5)
        self.assertFalse(result)
