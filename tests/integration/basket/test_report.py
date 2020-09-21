import datetime

from django.test import TestCase

from oscar.apps.basket.reports import (
    OpenBasketReportGenerator, SubmittedBasketReportGenerator)
from oscar.core.loading import get_model
from oscar.test.factories import BasketFactory

Basket = get_model('basket', 'Basket')


class TestBasketReports(TestCase):
    def setUp(self) -> None:
        BasketFactory.create_batch(5, status=Basket.OPEN)
        BasketFactory.create_batch(6, status=Basket.SUBMITTED)

    def test_open_report_doesnt_error(self):
        data = {
            'start_date': datetime.date(2012, 5, 1),
            'end_date': datetime.date(2012, 5, 17),
            'formatter': 'CSV'
        }
        generator = OpenBasketReportGenerator(**data)
        generator.generate()

    def test_open_report_queryset(self):
        generator = OpenBasketReportGenerator()
        assert generator.queryset.count() == 5

    def test_submitted_report_doesnt_error(self):
        data = {
            'start_date': datetime.date(2012, 5, 1),
            'end_date': datetime.date(2012, 5, 17),
            'formatter': 'CSV'
        }
        generator = SubmittedBasketReportGenerator(**data)
        generator.generate()

    def test_submitted_report_queryset(self):
        generator = SubmittedBasketReportGenerator()
        assert generator.queryset.count() == 6
