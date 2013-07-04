from django import test
from django_dynamic_fixture import G

from oscar.apps.catalogue.models import Product, ProductClass
from oscar.apps.partner.models import StockRecord


class TestAStandaloneProductIsAvailableToBuyWhen(test.TestCase):

    def test_its_product_class_does_not_track_stock(self):
        product_class = G(ProductClass, track_stock=False)
        product = G(Product, product_class=product_class)
        self.assertTrue(product.is_available_to_buy)

    def test_its_stockrecord_indicates_so(self):
        product = G(Product)
        record = G(StockRecord, product=product, num_in_stock=5)
        self.assertTrue(product.is_available_to_buy)


class TestAStandaloneProductIsNotAvailableToBuyWhen(test.TestCase):

    def test_it_has_no_stock_record(self):
        product = G(Product)
        self.assertFalse(product.is_available_to_buy)

    def test_its_stockrecord_indicates_so(self):
        product = G(Product)
        record = G(StockRecord, product=product, num_in_stock=0)
        self.assertFalse(product.is_available_to_buy)
