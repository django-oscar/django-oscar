import datetime
import time

from django.test import TestCase

from oscar.apps.dashboard.orders import forms


class TestOrderStatsForm(TestCase):
    def test_returns_inclusive_date_filters(self):
        data = {"date_from": "2012-08-03", "date_to": "2012-08-03"}
        form = forms.OrderStatsForm(data)
        self.assertTrue(form.is_valid())
        filters = form.get_filters()
        expected = datetime.date(*time.strptime("2012-08-04", "%Y-%m-%d")[0:3])
        self.assertEqual(expected, filters["date_placed__range"][1])
