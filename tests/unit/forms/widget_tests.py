from django.test import TestCase

from oscar.forms import widgets


class TestWidgetsDatetimeFormat(TestCase):

    def test_datetime_to_date_format_conversion(self):
        format_testcases = (
            ('%Y-%m-%d', 'yyyy-mm-dd'),
            ('%Y-%m-%d %H:%M', 'yyyy-mm-dd'),
        )
        for format_, expected in format_testcases:
            self.assertEqual(widgets.datetime_format_to_js_date_format(format_), expected)

    def test_datetime_to_time_format_conversion(self):
        format_testcases = (
            ('%Y-%m-%d %H:%M', 'hh:ii'),
            ('%H:%M', 'hh:ii'),
        )
        for format_, expected in format_testcases:
            self.assertEqual(widgets.datetime_format_to_js_time_format(format_), expected)