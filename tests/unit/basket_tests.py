import datetime

from django.test import TestCase

from oscar.apps.basket.models import Basket, Line
from oscar.test.helpers import create_product
from oscar.apps.basket.reports import (
    OpenBasketReportGenerator, SubmittedBasketReportGenerator)


class BasketModelTest(TestCase):

    def setUp(self):
        self.basket = Basket.objects.create()
        self.dummy_product = create_product()

    def test_empty_baskets_have_zero_lines(self):
        self.assertTrue(Basket().num_lines == 0)

    def test_new_baskets_are_empty(self):
        self.assertTrue(Basket().is_empty)

    def test_basket_have_with_one_line(self):
        Line.objects.create(basket=self.basket, product=self.dummy_product)
        self.assertTrue(self.basket.num_lines == 1)

    def test_add_product_creates_line(self):
        self.basket.add_product(self.dummy_product)
        self.assertTrue(self.basket.num_lines == 1)

    def test_adding_multiproduct_line_returns_correct_number_of_items(self):
        self.basket.add_product(self.dummy_product, 10)
        self.assertEqual(self.basket.num_items, 10)


class BasketReportTests(TestCase):

    def test_open_report_doesnt_error(self):
        data = {
            'start_date': datetime.date(2012, 5, 1),
            'end_date': datetime.date(2012, 5, 17),
            'formatter': 'CSV'
        }
        generator = OpenBasketReportGenerator(**data)
        generator.generate()

    def test_submitted_report_doesnt_error(self):
        data = {
            'start_date': datetime.date(2012, 5, 1),
            'end_date': datetime.date(2012, 5, 17),
            'formatter': 'CSV'
        }
        generator = SubmittedBasketReportGenerator(**data)
        generator.generate()
