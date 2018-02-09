# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase

from oscar.forms import widgets


class TimePickerInputTestCase(TestCase):

    def test_div_attrs_context(self):
        i = widgets.TimePickerInput(format='%H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['div_attrs'], {
            'data-oscarWidget': 'time',
            'data-timeFormat': 'hh:ii',
        })

    def test_icon_classes_context(self):
        i = widgets.TimePickerInput(format='%H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['icon_classes'], 'icon-time glyphicon-time')

    def test_input_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.TimePickerInput(format=u'τ-%H:%M')
        time = datetime.time(10, 47)
        html = i.render('time', time)
        self.assertIn(u'value="τ-10:47"', html)


class DatePickerInputTestCase(TestCase):

    def test_div_attrs_context(self):
        i = widgets.DatePickerInput(format='%d/%m/%Y')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['div_attrs'], {
            'data-oscarWidget': 'date',
            'data-dateFormat': 'dd/mm/yyyy',
        })

    def test_icon_classes_context(self):
        i = widgets.DatePickerInput(format='%H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['icon_classes'], 'icon-calendar glyphicon-calendar')

    def test_datepickerinput_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.DatePickerInput(format=u'δ-%d/%m/%Y')
        date = datetime.date(2017, 5, 1)
        html = i.render('date', date)
        self.assertIn(u'value="δ-01/05/2017"', html)


class DateTimePickerInputTestCase(TestCase):

    def test_div_attrs_context(self):
        i = widgets.DateTimePickerInput(format='%d/%m/%Y %H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['div_attrs'], {
            'data-oscarWidget': 'datetime',
            'data-datetimeFormat': 'dd/mm/yyyy hh:ii',
        })

    def test_icon_classes_context(self):
        i = widgets.DateTimePickerInput(format='%d/%m/%Y %H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['icon_classes'], 'icon-calendar glyphicon-calendar')

    def test_datetimepickerinput_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.DateTimePickerInput(format=u'δ-%d/%m/%Y %H:%M')
        date = datetime.datetime(2017, 5, 1, 10, 57)
        html = i.render('datetime', date)
        self.assertIn(u'value="δ-01/05/2017 10:57"', html)


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


class AdvancedSelectWidgetTestCase(TestCase):

    def test_widget_disabled_options(self):

        choices = (
            ('red', 'Red'),
            ('blue', 'Blue'),
            ('green', 'Green'),
        )

        disabled_values = ('red', 'green')

        i = widgets.AdvancedSelect(choices=choices, disabled_values=disabled_values)
        html = i.render('advselect', [])
        self.assertInHTML('<option value="blue">Blue</option>', html, count=1)
        self.assertInHTML('<option value="red" disabled>Red</option>', html, count=1)
        self.assertInHTML('<option value="green" disabled>Green</option>', html, count=1)
