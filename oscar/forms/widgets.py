from django.core.files.uploadedfile import InMemoryUploadedFile
import re
import six

from django import forms
from django.forms.util import flatatt
from django.forms.widgets import FileInput
from django.template import Context
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

try:
    from django.utils.html import format_html
except ImportError:
    # Django 1.4 compatibility
    from oscar.core.compat import format_html


class ImageInput(FileInput):
    """
    Widget providing a input element for file uploads based on the
    Django ``FileInput`` element. It hides the actual browser-specific
    input element and shows the available image for images that have
    been previously uploaded. Selecting the image will open the file
    dialog and allow for selecting a new or replacing image file.
    """
    template_name = 'partials/image_input_widget.html'
    attrs = {'accept': 'image/*'}

    def render(self, name, value, attrs=None):
        """
        Render the ``input`` field based on the defined ``template_name``. The
        image URL is take from *value* and is provided to the template as
        ``image_url`` context variable relative to ``MEDIA_URL``. Further
        attributes for the ``input`` element are provide in ``input_attrs`` and
        contain parameters specified in *attrs* and *name*.
        If *value* contains no valid image URL an empty string will be provided
        in the context.
        """
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if not value or isinstance(value, InMemoryUploadedFile):
            # can't display images that aren't stored
            image_url = ''
        else:
            image_url = final_attrs['value'] = force_text(
                self._format_value(value))

        return render_to_string(self.template_name, Context({
            'input_attrs': flatatt(final_attrs),
            'image_url': image_url,
            'image_id': "%s-image" % final_attrs['id'],
        }))


class WYSIWYGTextArea(forms.Textarea):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('class', '')
        kwargs['attrs']['class'] += ' wysiwyg'
        super(WYSIWYGTextArea, self).__init__(*args, **kwargs)


def datetime_format_to_js_date_format(format):
    """
    Convert a Python datetime format to a date format suitable for use with JS
    date pickers
    """
    converted = format
    replacements = {
        '%Y': 'yy',
        '%m': 'mm',
        '%d': 'dd',
        '%H:%M': '',
    }
    for search, replace in six.iteritems(replacements):
        converted = converted.replace(search, replace)
    return converted.strip()


def datetime_format_to_js_time_format(format):
    """
    Convert a Python datetime format to a time format suitable for use with JS
    date pickers
    """
    converted = format
    replacements = {
        '%Y': '',
        '%m': '',
        '%d': '',
        '%H': 'HH',
        '%M': 'mm',
    }
    for search, replace in six.iteritems(replacements):
        converted = converted.replace(search, replace)

    converted = re.sub('[-/][^%]', '', converted)

    return converted.strip()


def add_js_formats(widget):
    """
    Set data attributes for date and time format on a widget
    """
    attrs = {
        'data-dateFormat': datetime_format_to_js_date_format(
            widget.format),
        'data-timeFormat': datetime_format_to_js_time_format(
            widget.format)
    }
    widget.attrs.update(attrs)


class DatePickerInput(forms.DateInput):
    """
    DatePicker input that uses the jQuery UI datepicker.  Data attributes are
    used to pass the date format to the JS
    """
    def __init__(self, *args, **kwargs):
        super(DatePickerInput, self).__init__(*args, **kwargs)
        add_js_formats(self)


class DateTimePickerInput(forms.DateTimeInput):
    # Build a widget which uses the locale datetime format but without seconds.
    # We also use data attributes to pass these formats to the JS datepicker.

    def __init__(self, *args, **kwargs):
        include_seconds = kwargs.pop('include_seconds', False)
        super(DateTimePickerInput, self).__init__(*args, **kwargs)

        if not include_seconds:
            self.format = re.sub(':?%S', '', self.format)
        add_js_formats(self)


class AdvancedSelect(forms.Select):
    """
    Customised Select widget that allows a list of disabled values to be passed
    to the constructor.  Django's default Select widget doesn't allow this so
    we have to override the render_option method and add a section that checks
    for whether the widget is disabled.
    """

    def __init__(self, attrs=None, choices=(), disabled_values=()):
        self.disabled_values = set(force_text(v) for v in disabled_values)
        super(AdvancedSelect, self).__init__(attrs, choices)

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_text(option_value)
        if option_value in self.disabled_values:
            selected_html = mark_safe(' disabled="disabled"')
        elif option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html(u'<option value="{0}"{1}>{2}</option>',
                           option_value,
                           selected_html,
                           force_text(option_label))
