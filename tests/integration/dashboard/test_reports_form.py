import json

from django.test import TestCase

from oscar.apps.dashboard.reports import forms
from oscar.apps.order.reports import OrderReportGenerator


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

    def test_date_range_on_report_without_date_range_support(self):
        form = forms.ReportForm(
            data={"date_from": "2016-11-02", "report_type": "product_analytics"}
        )
        self.assertFalse(form.is_valid())
        form = forms.ReportForm(
            data={"date_to": "2016-11-03", "report_type": "product_analytics"}
        )
        self.assertFalse(form.is_valid())

    def test_no_date_range_on_report_without_date_range_support(self):
        form = forms.ReportForm(data={"report_type": "product_analytics"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_unsupported_fields_are_exposed_to_js(self):
        form = forms.ReportForm()
        attrs = form.fields["report_type"].widget.attrs
        unsupported_fields = json.loads(attrs["data-unsupported-fields"])
        self.assertEqual(
            set(unsupported_fields),
            {"product_analytics", "user_analytics", "vouchers", "conditional-offers"},
        )
        self.assertEqual(
            unsupported_fields["product_analytics"], ["id_date_from", "id_date_to"]
        )

    def test_generator_can_declare_other_unsupported_fields(self):
        class NoDownloadReportGenerator(OrderReportGenerator):
            code = "no_download"

            @classmethod
            def get_unsupported_form_fields(cls):
                return super().get_unsupported_form_fields() + ["download"]

        class NoDownloadReportForm(forms.ReportForm):
            generators = forms.ReportForm.generators + [NoDownloadReportGenerator]

        def get_form(data):
            form = NoDownloadReportForm(data=data)
            form.fields["report_type"].choices = [
                (generator.code, generator.description)
                for generator in NoDownloadReportForm.generators
            ]
            return form

        form = get_form({"report_type": "no_download", "date_from": "2016-11-02"})
        self.assertTrue(form.is_valid(), form.errors)
        form = get_form({"report_type": "no_download", "download": "on"})
        self.assertFalse(form.is_valid())
