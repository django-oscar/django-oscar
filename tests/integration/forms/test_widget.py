import datetime

from django import forms
from django.test import TestCase
from django.urls import reverse_lazy

from oscar.apps.catalogue.models import Product
from oscar.forms import widgets
from oscar.test.factories import create_product


class ImageInputTestCase(TestCase):

    def test_unbound_context(self):
        i = widgets.ImageInput()
        ctx = i.get_context('test_input', None, {'id': 'test-image-id'})
        self.assertEqual(ctx['image_id'], 'test-image-id-image')
        self.assertEqual(ctx['image_url'], '')
        self.assertEqual(
            ctx['widget']['attrs'],
            {'accept': 'image/*', 'id': 'test-image-id'}
        )

    def test_bound_context(self):
        i = widgets.ImageInput()
        ctx = i.get_context('test_input', '/dummy-image-value', {'id': 'test-image-id'})
        self.assertEqual(ctx['image_url'], '/dummy-image-value')


class TimePickerInputTestCase(TestCase):

    def test_div_attrs_context(self):
        i = widgets.TimePickerInput(format='%H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['div_attrs'], {
            'data-oscarWidget': 'time',
            'data-timeFormat': 'HH:mm',
        })

    def test_icon_classes_context(self):
        i = widgets.TimePickerInput(format='%H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['icon_classes'], 'far fa-clock')

    def test_input_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.TimePickerInput(format='τ-%H:%M')
        time = datetime.time(10, 47)
        html = i.render('time', time)
        self.assertIn('value="τ-10:47"', html)


class DatePickerInputTestCase(TestCase):

    def test_div_attrs_context(self):
        i = widgets.DatePickerInput(format='%d/%m/%Y')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['div_attrs'], {
            'data-oscarWidget': 'date',
            'data-dateFormat': 'DD/MM/YYYY',
        })

    def test_icon_classes_context(self):
        i = widgets.DatePickerInput(format='%H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['icon_classes'], 'far fa-calendar-alt')

    def test_datepickerinput_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.DatePickerInput(format='δ-%d/%m/%Y')
        date = datetime.date(2017, 5, 1)
        html = i.render('date', date)
        self.assertIn('value="δ-01/05/2017"', html)


class DateTimePickerInputTestCase(TestCase):

    def test_div_attrs_context(self):
        i = widgets.DateTimePickerInput(format='%d/%m/%Y %H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['div_attrs'], {
            'data-oscarWidget': 'datetime',
            'data-datetimeFormat': 'DD/MM/YYYY HH:mm',
        })

    def test_icon_classes_context(self):
        i = widgets.DateTimePickerInput(format='%d/%m/%Y %H:%M')
        ctx = i.get_context('test_input', None, {})
        self.assertEqual(ctx['icon_classes'], 'far fa-calendar-alt')

    def test_datetimepickerinput_format_unicode(self):
        # Check that the widget can handle unicode formats
        i = widgets.DateTimePickerInput(format='δ-%d/%m/%Y %H:%M')
        date = datetime.datetime(2017, 5, 1, 10, 57)
        html = i.render('datetime', date)
        self.assertIn('value="δ-01/05/2017 10:57"', html)


class TestWidgetsDatetimeFormat(TestCase):

    def test_datetime_to_date_format_conversion(self):
        format_testcases = (
            ('%Y-%m-%d', 'YYYY-MM-DD'),
            ('%Y-%m-%d %H:%M', 'YYYY-MM-DD'),
        )
        for format_, expected in format_testcases:
            self.assertEqual(widgets.datetime_format_to_js_date_format(format_), expected)

    def test_datetime_to_time_format_conversion(self):
        format_testcases = (
            ('%Y-%m-%d %H:%M', 'HH:mm'),
            ('%H:%M', 'HH:mm'),
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


class RemoteSelectTestCase(TestCase):

    def setUp(self):
        self.url = reverse_lazy('dashboard:catalogue-product-lookup')

    def _get_form_field(self, **kwargs):
        return forms.ModelChoiceField(
            queryset=Product.objects.all(),
            widget=widgets.RemoteSelect(lookup_url=self.url),
            **kwargs
        )

    def _get_multiselect_form_field(self, **kwargs):
        return forms.ModelChoiceField(
            queryset=Product.objects.all(),
            widget=widgets.MultipleRemoteSelect(lookup_url=self.url),
            **kwargs
        )

    def test_remote_url_required(self):
        with self.assertRaises(ValueError):
            widgets.RemoteSelect()

    def test_select_widget_renders_only_selected_choices(self):
        create_product()
        p2 = create_product()

        field = self._get_form_field()
        form_choices = list(field.widget.options(name='name', value=[p2.pk]))
        # We should only have one choice, not two
        self.assertEqual(len(form_choices), 1)
        self.assertEqual(form_choices[0]['value'], p2.pk)

    def test_widget_attrs(self):
        field = self._get_form_field()
        attrs = field.widget.get_context(name='my_field', value=None, attrs={})['widget']['attrs']
        self.assertEqual(attrs['data-multiple'], '')
        self.assertEqual(attrs['data-required'], 'required')
        self.assertEqual(attrs['data-ajax-url'], self.url)

    def test_not_required_widget_attrs(self):
        field = self._get_multiselect_form_field(required=False)
        attrs = field.widget.get_context(name='my_field', value=None, attrs={})['widget']['attrs']
        self.assertEqual(attrs['data-required'], '')

    def test_multiselect_widget_renders_only_selected_choices(self):
        create_product()
        p2 = create_product()
        p3 = create_product()

        field = self._get_multiselect_form_field()
        form_choices = list(field.widget.options(name='name', value=[p2.pk, p3.pk]))
        # We should only have two choices, not three
        self.assertEqual(len(form_choices), 2)

    def test_multiselect_widget_attrs(self):
        field = self._get_multiselect_form_field()
        attrs = field.widget.get_context(name='my_field', value=None, attrs={})['widget']['attrs']
        self.assertEqual(attrs['data-multiple'], 'multiple')
