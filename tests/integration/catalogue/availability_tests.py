from django import test
import mock

from oscar.apps.catalogue import models
from oscar.apps.partner.models import StockRecord


class TestAStandaloneProductIsAvailableToBuyWhen(test.TestCase):

    def test_its_product_class_does_not_track_stock(self):
        product_class = models.ProductClass(
            track_stock=False)
        product = models.Product(
            product_class=product_class)
        self.assertTrue(product.is_available_to_buy)

    def test_its_stockrecord_indicates_so(self):
        product_class = models.ProductClass()
        product = models.Product(
            id=-1,  # Required so Django doesn't raise ValueError
            product_class=product_class)

        # Create mock version of a model that can be assigned as a FK
        record = mock.Mock(spec=StockRecord)
        record._state = mock.Mock()
        record._state.db = None
        record.is_available_to_buy = True
        product.stockrecord = record

        self.assertTrue(product.is_available_to_buy)


class TestAStandaloneProductIsNotAvailableToBuyWhen(test.TestCase):

    def test_it_has_no_stock_record(self):
        product_class = models.ProductClass()
        product = models.Product(
            id=-1,
            product_class=product_class)
        self.assertFalse(product.is_available_to_buy)

    def test_its_stockrecord_indicates_so(self):
        product_class = models.ProductClass()
        product = models.Product(
            id=-1,
            product_class=product_class)

        # Create mock version of a model that can be assigned as a FK
        record = mock.Mock(spec=StockRecord)
        record._state = mock.Mock()
        record._state.db = None
        record.is_available_to_buy = False
        product.stockrecord = record

        self.assertFalse(product.is_available_to_buy)
