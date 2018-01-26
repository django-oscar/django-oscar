# -*- coding: utf-8 -*-
import datetime
from unittest import skipIf

from django import forms, VERSION
from django.test import TestCase

from oscar.apps.catalogue.models import Product
from django.core.urlresolvers import reverse_lazy
from oscar.forms import widgets
from oscar.test.factories import create_product


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


class RemoteSelectTestCase(TestCase):

    def test_remote_url_required(self):
        with self.assertRaises(ValueError):
            i = widgets.RemoteSelect()

    @skipIf(VERSION < (1, 11), "Test widget in Django 1.11 and above")
    def test_widget_renders_only_selected_choices(self):
        p1 = create_product()
        p2 = create_product()

        f = forms.ModelChoiceField(
            queryset=Product.objects.all(),
            widget=widgets.RemoteSelect(lookup_url=reverse_lazy('dashboard:catalogue-product-lookup'))
        )

        form_choices = list(f.widget.options(name='name', value=[p2.pk]))

        # We should only have one choice, not two
        self.assertEqual(len(form_choices), 1)
        self.assertEqual(form_choices[0]['value'], p2.pk)

    @skipIf(VERSION >= (1, 9), "Test widget in Django 1.8 and above")
    def test_django18_widget_renders_only_selected_choices(self):
        p1 = create_product()
        p2 = create_product()

        f = forms.ModelChoiceField(
            queryset=Product.objects.all(),
            widget=widgets.RemoteSelect(lookup_url=reverse_lazy('dashboard:catalogue-product-lookup'))
        )

        html = f.widget.render(name='name', value=p2.pk)

        # We should only have one choice, not two
        self.assertHTMLEqual(html, '''<select name="name">
                                  <option value="{}" selected="selected">{}</option>
                                  </select>'''.format(p2.pk, p2.title))
