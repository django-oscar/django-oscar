# -*- coding: utf-8 -*-
import datetime

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

    def test_timepickerinput_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.TimePickerInput(format=u'τ-%H:%M')
        time = datetime.time(10, 47)
        html = i.render('time', time)
        self.assertIn(u'value="τ-10:47"', html)

    def test_datepickerinput_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.DatePickerInput(format=u'δ-%d/%m/%Y')
        date = datetime.date(2017, 5, 1)
        html = i.render('date', date)
        self.assertIn(u'value="δ-01/05/2017"', html)

    def test_datetimepickerinput_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.DateTimePickerInput(format=u'δ-%d/%m/%Y %H:%M')
        date = datetime.datetime(2017, 5, 1, 10, 57)
        html = i.render('datetime', date)
        self.assertIn(u'value="δ-01/05/2017 10:57"', html)
