from django.test import TestCase

from oscar.apps.dashboard.reports import forms


class TestReportsForm(TestCase):
    def test_date_range_empty(self):
        form = forms.ReportForm(data={})
        self.assertFalse(form.is_valid())

    def test_date_range_complete(self):
        form = forms.ReportForm(
            data={
                "date_from": "2016-11-02",
                "date_to": "2016-11-03",
                "report_type": "order_report",
            }
        )
        self.assertTrue(form.is_valid())

    def test_date_range_incomplete(self):
        form = forms.ReportForm(
            data={
                "report_type": "order_report",
                "date_to": "",
                "date_from": "2016-11-02",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        form = forms.ReportForm(
            data={
                "date_from": "",
                "date_to": "2016-11-03",
                "report_type": "order_report",
            }
        )
        self.assertTrue(form.is_valid())
        form = forms.ReportForm(
            data={"date_from": "2016-11-02", "report_type": "order_report"}
        )
        self.assertTrue(form.is_valid())
        form = forms.ReportForm(
            data={"date_to": "2016-11-03", "report_type": "order_report"}
        )
        self.assertTrue(form.is_valid())

    def test_date_range_incorrect(self):
        form = forms.ReportForm(
            data={
                "date_from": "2016-11-03",
                "date_to": "2016-11-02",
                "report_type": "order_report",
            }
        )
        self.assertFalse(form.is_valid())
