import datetime

from django.test import TestCase
from django.utils.timezone import utc
from freezegun import freeze_time

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

    @freeze_time('2020-05-02')
    def test_open_report_filtering_by_date_range(self):
        BasketFactory.create(status=Basket.OPEN)
        data = {
            'start_date': datetime.date(2020, 5, 1),
            'end_date': datetime.date(2020, 6, 1),
            'formatter': 'CSV'
        }
        generator = OpenBasketReportGenerator(**data)
        assert generator.queryset.count() == 1

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

    def test_submitted_report_filtering_by_date_range(self):
        date_submitted = datetime.datetime(2020, 7, 3).replace(tzinfo=utc)
        BasketFactory.create(status=Basket.SUBMITTED, date_submitted=date_submitted)
        data = {
            'start_date': datetime.date(2020, 7, 1),
            'end_date': datetime.date(2020, 8, 1),
            'formatter': 'CSV'
        }
        generator = SubmittedBasketReportGenerator(**data)
        assert generator.queryset.count() == 1
