from decimal import Decimal as D

from django.test import TestCase

from oscar.test.helpers import create_product
from oscar.apps.basket.models import Basket
from oscar.apps.partner.models import StockRecord, StockAlert
from oscar.apps.order.utils import OrderCreator


# These aren't really unit tests - move them?
class TestPlacingAnOrder(TestCase):

    def setUp(self):
        self.product = create_product(price=D('12.00'), num_in_stock=5)
        self.basket = Basket()
        self.basket.add_product(self.product)

    def set_threshold(self, threshold):
        self.product.stockrecord.low_stock_threshold = threshold
        self.product.stockrecord.save()

    def test_correctly_allocates_stock(self):
        OrderCreator().place_order(self.basket)

        record = StockRecord.objects.get(product=self.product)
        self.assertEqual(5, record.num_in_stock)
        self.assertEqual(1, record.num_allocated)
        self.assertEqual(4, record.net_stock_level)

    def test_does_not_raise_an_alert_if_threshold_not_broken(self):
        self.set_threshold(4)
        OrderCreator().place_order(self.basket)

        alerts = StockAlert.objects.all()
        self.assertEqual(0, len(alerts))

    def test_raises_alert_when_threshold_is_reached(self):
        self.set_threshold(5)
        OrderCreator().place_order(self.basket)

        alerts = StockAlert.objects.filter(
            stockrecord=self.product.stockrecord)
        self.assertEqual(1, len(alerts))

    def test_only_raises_an_alert_once(self):
        self.set_threshold(5)
        StockAlert.objects.create(stockrecord=self.product.stockrecord,
                                  threshold=10)
        OrderCreator().place_order(self.basket)

        alerts = StockAlert.objects.filter(
            stockrecord=self.product.stockrecord)
        self.assertEqual(1, len(alerts))


class TestRestockingProduct(TestCase):

    def setUp(self):
        self.product = create_product(price=D('12.00'), num_in_stock=5)
        self.basket = Basket()
        self.basket.add_product(self.product)

    def set_threshold(self, threshold):
        self.product.stockrecord.low_stock_threshold = threshold
        self.product.stockrecord.save()

    def test_closes_open_alert(self):
        self.set_threshold(5)
        OrderCreator().place_order(self.basket)

        alert = StockAlert.objects.get(stockrecord=self.product.stockrecord)
        self.assertEqual(StockAlert.OPEN, alert.status)

        # Restock product
        self.product.stockrecord.num_in_stock = 15
        self.product.stockrecord.save()

        alert = StockAlert.objects.get(stockrecord=self.product.stockrecord)
        self.assertEqual(StockAlert.CLOSED, alert.status)
