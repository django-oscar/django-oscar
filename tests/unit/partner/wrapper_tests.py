import datetime

from django.test import TestCase
from mock import patch

from oscar.apps.partner.wrappers import DefaultWrapper
from oscar.apps.partner.models import StockRecord
from oscar.test.helpers import create_product


class TestDefaultWrapper(TestCase):

    def setUp(self):
        self.wrapper = DefaultWrapper()
        self.product = create_product()

    def test_num_in_stock_is_none_is_available_to_buy(self):
        record = StockRecord(num_in_stock=None, product=self.product)
        self.assertTrue(self.wrapper.is_available_to_buy(record))

    def test_zero_stock_is_not_available_to_buy(self):
        record = StockRecord(num_in_stock=0, product=self.product)
        self.assertFalse(self.wrapper.is_available_to_buy(record))

    def test_nonzero_stock_is_available_to_buy(self):
        record = StockRecord(num_in_stock=10, product=self.product)
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

    def test_max_purchase_quantity(self):
        record = StockRecord(num_in_stock=4, product=self.product)
        self.assertEqual(record.num_in_stock, self.wrapper.max_purchase_quantity(record))

    def test_availability_code_for_in_stock(self):
        record = StockRecord(num_in_stock=4, product=self.product)
        self.assertEqual('instock', self.wrapper.availability_code(record))

    def test_availability_code_for_zero_stock(self):
        record = StockRecord(num_in_stock=0, product=self.product)
        self.assertEqual('outofstock', self.wrapper.availability_code(record))

    def test_availability_code_for_null_stock_but_available(self):
        record = StockRecord(num_in_stock=None, product=self.product)
        self.assertEqual('available', self.wrapper.availability_code(record))

    def test_availability_message_for_in_stock(self):
        record = StockRecord(num_in_stock=4, product=self.product)
        self.assertEqual(u'In stock (4 available)', unicode(self.wrapper.availability(record)))

    def test_availability_message_for_available(self):
        record = StockRecord(num_in_stock=None, product=self.product)
        self.assertEqual(u'Available', unicode(self.wrapper.availability(record)))

    def test_availability_message_for_out_of_stock(self):
        record = StockRecord(num_in_stock=0, product=self.product)
        self.assertEqual(u'Not available', unicode(self.wrapper.availability(record)))

    def test_backorder_purchase_is_permitted(self):
        record = StockRecord(num_in_stock=None, product=self.product)
        with patch.object(self.wrapper, 'max_purchase_quantity') as m:
            m.return_value = None
            result, reason = self.wrapper.is_purchase_permitted(record)
            self.assertTrue(result)
