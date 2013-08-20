from django.test import TestCase

from oscar.apps.partner import availability
from oscar.test import factories


class TestDelegateToStockRecordWrapper(TestCase):

    def setUp(self):
        self.product = factories.create_product()
        self.stockrecord = factories.create_stockrecord(self.product)
        self.assertTrue(self.product.get_product_class().track_stock)

        self.availability = availability.DelegateToStockRecord(
            self.product, self.stockrecord)

    def test_delegates_is_available_to_buy(self):
        self.assertEquals(
            self.stockrecord.is_available_to_buy,
            self.availability.is_available_to_buy)

    def test_delegates_is_purchase_permitted(self):
        self.assertEquals(
            self.stockrecord.is_purchase_permitted(1),
            self.availability.is_purchase_permitted(quantity=1))

    def test_delegates_availability_code(self):
        self.assertEquals(
            self.stockrecord.availability_code,
            self.availability.code)

    def test_delegates_availability_message(self):
        self.assertEquals(
            self.stockrecord.availability,
            self.availability.message)

    def test_delegates_lead_time(self):
        self.assertEquals(
            self.stockrecord.lead_time,
            self.availability.lead_time)

    def test_delegates_dispatch_date(self):
        self.assertEquals(
            self.stockrecord.dispatch_date,
            self.availability.dispatch_date)


class TestStockRequiredWrapperForRecordWithStock(TestCase):

    def setUp(self):
        self.product = factories.create_product()
        self.stockrecord = factories.create_stockrecord(
            self.product, num_in_stock=5)
        self.availability = availability.StockRequired(
            self.stockrecord)

    def test_is_available_to_buy(self):
        self.assertTrue(self.availability.is_available_to_buy)

    def test_permits_purchases_up_to_stock_level(self):
        for x in range(0, 6):
            is_permitted, __ = self.availability.is_purchase_permitted(x)
            self.assertTrue(is_permitted)

    def test_forbids_purchases_over_stock_level(self):
        is_permitted, __ = self.availability.is_purchase_permitted(7)
        self.assertFalse(is_permitted)

    def test_returns_correct_code(self):
        self.assertEquals('instock', self.availability.code)

    def test_returns_correct_message(self):
        self.assertEquals('In stock (5 available)', self.availability.message)


class TestStockRequiredWrapperForRecordWithoutStock(TestCase):

    def setUp(self):
        self.product = factories.create_product()
        self.stockrecord = factories.create_stockrecord(
            self.product, num_in_stock=0)
        self.availability = availability.StockRequired(
            self.stockrecord)

    def test_is_available_to_buy(self):
        self.assertFalse(self.availability.is_available_to_buy)

    def test_forbids_purchases(self):
        is_permitted, __ = self.availability.is_purchase_permitted(1)
        self.assertFalse(is_permitted)

    def test_returns_correct_code(self):
        self.assertEquals('outofstock', self.availability.code)

    def test_returns_correct_message(self):
        self.assertEquals('Not available', self.availability.message)


class TestAvailableWrapper(TestCase):

    def setUp(self):
        self.availability = availability.Available()

    def test_is_available_to_buy(self):
        self.assertTrue(self.availability.is_available_to_buy)

    def test_permits_any_purchase(self):
        is_permitted, __ = self.availability.is_purchase_permitted(10000)
        self.assertTrue(is_permitted)

    def test_returns_correct_code(self):
        self.assertEquals('available', self.availability.code)

    def test_returns_correct_message(self):
        self.assertEquals('Available', self.availability.message)
