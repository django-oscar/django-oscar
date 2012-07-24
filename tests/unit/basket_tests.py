import datetime

from django.test import TestCase
from django.test.client import RequestFactory

from oscar.apps.basket.models import Basket
from oscar.apps.basket.middleware import BasketMiddleware
from oscar.test.helpers import create_product
from oscar.apps.basket.reports import (
    OpenBasketReportGenerator, SubmittedBasketReportGenerator)


class TestBasketModel(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.product = create_product()

    def test_an_empty_basket_has_zero_lines(self):
        self.assertEqual(0, self.basket.num_lines)

    def test_new_baskets_are_empty(self):
        self.assertTrue(self.basket.is_empty)

    def test_adding_product_creates_line(self):
        self.basket.add_product(self.product)
        self.assertEqual(1, self.basket.num_lines)

    def test_adding_multiproduct_line_returns_correct_number_of_items(self):
        self.basket.add_product(self.product, 10)
        self.assertEqual(self.basket.num_items, 10)
        self.assertEqual(self.basket.num_lines, 1)

    def test_add_product_creates_line(self):
        self.basket.add_product(self.product)
        self.assertTrue(self.basket.num_lines == 1)

    def test_flushing_basket_removes_all_lines(self):
        self.basket.add_product(self.product, 10)
        self.assertEqual(self.basket.num_items, 10)
        self.basket.flush()
        self.assertEqual(self.basket.num_items, 0)


class TestBasketMiddleware(TestCase):

    def setUp(self):
        self.middleware = BasketMiddleware()

    def test_basket_is_attached_to_request(self):
        req = RequestFactory().get('/')
        self.middleware.process_request(req)
        self.assertTrue(hasattr(req, 'basket'))


class TestBasketReports(TestCase):

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
