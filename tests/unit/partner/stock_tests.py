from decimal import Decimal as D

from django.test import TestCase

from oscar.test.helpers import create_product
from oscar.apps.basket.models import Basket
from oscar.apps.partner.models import StockRecord, StockAlert
from oscar.apps.order.utils import OrderCreator


class StockActionTests(TestCase):

    def setUp(self):
        self.product = create_product(price=D('12.00'), num_in_stock=5)
        self.basket = Basket()
        self.basket.add_product(self.product)

    def tearDown(self):
        StockAlert.objects.all().delete()

    def set_threshold(self, threshold):
        self.product.stockrecord.low_stock_threshold = threshold
        self.product.stockrecord.save()

    def test_stock_is_allocated_after_checkout(self):
        order = OrderCreator().place_order(self.basket)

        record = StockRecord.objects.get(product=self.product)
        self.assertEqual(5, record.num_in_stock)
        self.assertEqual(1, record.num_allocated)
        self.assertEqual(4, record.net_stock_level)

    def test_no_alert_raised_if_threshold_not_breached(self):
        self.set_threshold(3)
        order = OrderCreator().place_order(self.basket)

        alerts = StockAlert.objects.all()
        self.assertEqual(0, len(alerts))

    def test_alert_created_when_threhold_met(self):
        self.set_threshold(5)
        order = OrderCreator().place_order(self.basket)

        alerts = StockAlert.objects.filter(stockrecord=self.product.stockrecord)
        self.assertEqual(1, len(alerts))

    def test_alert_only_created_when_no_alert_exists_already(self):
        self.set_threshold(5)
        StockAlert.objects.create(stockrecord=self.product.stockrecord,
                                  threshold=10)
        order = OrderCreator().place_order(self.basket)

        alerts = StockAlert.objects.filter(stockrecord=self.product.stockrecord)
        self.assertEqual(1, len(alerts))

    def test_alert_closed_when_stock_replenished(self):
        self.set_threshold(5)
        order = OrderCreator().place_order(self.basket)

        alert = StockAlert.objects.get(stockrecord=self.product.stockrecord)
        self.assertEqual(StockAlert.OPEN, alert.status)

        self.product.stockrecord.num_in_stock = 15
        self.product.stockrecord.save()
        alert = StockAlert.objects.get(stockrecord=self.product.stockrecord)
        self.assertEqual(StockAlert.CLOSED, alert.status)
