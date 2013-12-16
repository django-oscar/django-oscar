from django.test import TestCase
from decimal import Decimal as D

from oscar.apps.partner import strategy
from oscar.apps.catalogue import models
from oscar.test import factories
from oscar.apps.basket.models import Line


class TestDefaultStrategy(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()

    def test_no_stockrecords(self):
        product = factories.create_product()
        info = self.strategy.fetch_for_product(product)
        self.assertFalse(info.availability.is_available_to_buy)
        self.assertIsNone(info.price.incl_tax)

    def test_one_stockrecord(self):
        product = factories.create_product(price=D('1.99'), num_in_stock=4)
        info = self.strategy.fetch_for_product(product)
        self.assertTrue(info.availability.is_available_to_buy)
        self.assertEquals(D('1.99'), info.price.excl_tax)
        self.assertEquals(D('1.99'), info.price.incl_tax)

    def test_product_which_doesnt_track_stock(self):
        product_class = models.ProductClass.objects.create(
            name="Digital", track_stock=False)
        product = factories.create_product(
            product_class=product_class,
            price=D('1.99'), num_in_stock=None)
        info = self.strategy.fetch_for_product(product)
        self.assertTrue(info.availability.is_available_to_buy)

    def test_line_method_is_same_as_product_one(self):
        product = factories.create_product()
        line = Line(product=product)
        info = self.strategy.fetch_for_line(line)
        self.assertFalse(info.availability.is_available_to_buy)
        self.assertIsNone(info.price.incl_tax)
