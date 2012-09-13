from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.partner.wrappers import DefaultWrapper
from oscar.apps.catalogue.models import Product, ProductClass
from oscar.apps.partner.models import StockRecord


class TestStockRecordWithNullStockLevel(TestCase):
    """
    Stock record with num_in_stock=None
    """

    def setUp(self):
        self.wrapper = DefaultWrapper()
        self.product = Product()
        self.product.product_class = ProductClass()
        self.record = StockRecord(num_in_stock=None, product=self.product)

    def test_is_available_to_buy(self):
        self.assertTrue(self.wrapper.is_available_to_buy(self.record))

    def test_permits_purchase(self):
        is_permitted, reason = self.wrapper.is_purchase_permitted(
            self.record)
        self.assertTrue(is_permitted)

    def test_has_no_max_purchase_quantity(self):
        self.assertIsNone(self.wrapper.max_purchase_quantity(self.record))

    def test_returns_available_code(self):
        self.assertEqual(DefaultWrapper.CODE_AVAILABLE,
                         self.wrapper.availability_code(self.record))

    def test_returns_correct_availability_message(self):
        self.assertEqual("Available",
                         self.wrapper.availability(self.record))

    def test_returns_no_estimated_dispatch_date(self):
        self.assertIsNone(self.wrapper.dispatch_date(self.record))

    def test_returns_no_estimated_lead_time(self):
        self.assertIsNone(self.wrapper.lead_time(self.record))

    def test_returns_zero_tax(self):
        self.assertEqual(D('0.00'), self.wrapper.calculate_tax(self.record))


class TestStockRecordOfDigitalProduct(TestCase):

    def setUp(self):
        self.wrapper = DefaultWrapper()
        self.product = Product()
        self.product.product_class = ProductClass(track_stock=False)
        self.record = StockRecord(num_in_stock=None, product=self.product)

    def test_is_available_to_buy(self):
        self.assertTrue(self.wrapper.is_available_to_buy(self.record))

    def test_permits_purchase(self):
        is_permitted, reason = self.wrapper.is_purchase_permitted(
            self.record)
        self.assertTrue(is_permitted)

    def test_has_no_max_purchase_quantity(self):
        self.assertIsNone(self.wrapper.max_purchase_quantity(self.record))

    def test_returns_available_code(self):
        self.assertEqual(DefaultWrapper.CODE_AVAILABLE,
                         self.wrapper.availability_code(self.record))

    def test_returns_correct_availability_message(self):
        self.assertEqual("Available",
                         self.wrapper.availability(self.record))

    def test_returns_no_estimated_dispatch_date(self):
        self.assertIsNone(self.wrapper.dispatch_date(self.record))

    def test_returns_no_estimated_lead_time(self):
        self.assertIsNone(self.wrapper.lead_time(self.record))

    def test_returns_zero_tax(self):
        self.assertEqual(D('0.00'), self.wrapper.calculate_tax(self.record))


class TestStockRecordOfZeroStockProduct(TestCase):

    def setUp(self):
        self.wrapper = DefaultWrapper()
        self.product = Product()
        self.product.product_class = ProductClass()
        self.record = StockRecord(num_in_stock=0, product=self.product)

    def test_is_not_available_to_buy(self):
        self.assertFalse(self.wrapper.is_available_to_buy(self.record))

    def test_does_not_permit_purchase(self):
        is_permitted, reason = self.wrapper.is_purchase_permitted(
            self.record)
        self.assertFalse(is_permitted)

    def test_has_zero_max_purchase_quantity(self):
        self.assertEqual(0, self.wrapper.max_purchase_quantity(self.record))

    def test_returns_unavailable_code(self):
        self.assertEqual(DefaultWrapper.CODE_UNAVAILABLE,
                         self.wrapper.availability_code(self.record))

    def test_returns_correct_availability_message(self):
        self.assertEqual("Not available",
                         self.wrapper.availability(self.record))

    def test_returns_no_estimated_dispatch_date(self):
        self.assertIsNone(self.wrapper.dispatch_date(self.record))

    def test_returns_no_estimated_lead_time(self):
        self.assertIsNone(self.wrapper.lead_time(self.record))

    def test_returns_zero_tax(self):
        self.assertEqual(D('0.00'), self.wrapper.calculate_tax(self.record))


class TestStockRecordWithPositiveStock(TestCase):

    def setUp(self):
        self.wrapper = DefaultWrapper()
        self.product = Product()
        self.product.product_class = ProductClass()
        self.record = StockRecord(num_in_stock=5, product=self.product)

    def test_is_available_to_buy(self):
        self.assertTrue(self.wrapper.is_available_to_buy(self.record))

    def test_does_permit_purchase_for_smaller_quantities(self):
        for x in range(1, 6):
            is_permitted, reason = self.wrapper.is_purchase_permitted(
                self.record, quantity=x)
            self.assertTrue(is_permitted)

    def test_does_not_permit_purchase_for_larger_quantities(self):
        for x in range(6, 10):
            is_permitted, reason = self.wrapper.is_purchase_permitted(
                self.record, quantity=x)
            self.assertFalse(is_permitted)

    def test_has_correct_max_purchase_quantity(self):
        self.assertEqual(5, self.wrapper.max_purchase_quantity(self.record))

    def test_returns_available_code(self):
        self.assertEqual(DefaultWrapper.CODE_IN_STOCK,
                         self.wrapper.availability_code(self.record))

    def test_returns_correct_availability_message(self):
        self.assertEqual("In stock (5 available)",
                         self.wrapper.availability(self.record))

    def test_returns_no_estimated_dispatch_date(self):
        self.assertIsNone(self.wrapper.dispatch_date(self.record))

    def test_returns_no_estimated_lead_time(self):
        self.assertIsNone(self.wrapper.lead_time(self.record))

    def test_returns_zero_tax(self):
        self.assertEqual(D('0.00'), self.wrapper.calculate_tax(self.record))
