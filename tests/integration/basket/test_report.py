import datetime

from django.test import TestCase

from oscar.apps.basket.reports import (
    OpenBasketReportGenerator, SubmittedBasketReportGenerator)


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
