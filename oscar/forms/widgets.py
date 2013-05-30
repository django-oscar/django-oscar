import re

from django.conf import settings
from django import forms
from django.template import Context
from django.forms.widgets import FileInput
from django.utils.encoding import force_unicode
from django.template.loader import render_to_string
from django.forms.util import flatatt


class ImageInput(FileInput):
    """
    Widget prodiving a input element for file uploads based on the
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
        if value is None:
            value = ''

        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))

        image_url = final_attrs.get('value', '')
        if image_url:
            image_url = "%s/%s" % (settings.MEDIA_URL, image_url)

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
    for search, replace in replacements.iteritems():
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
    for search, replace in replacements.iteritems():
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
