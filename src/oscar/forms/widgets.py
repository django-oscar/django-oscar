import re

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms.models import ModelChoiceIterator
from django.forms.widgets import FileInput
from django.utils import formats
from django.utils.encoding import force_text


class ImageInput(FileInput):
    """
    Widget providing a input element for file uploads based on the
    Django ``FileInput`` element. It hides the actual browser-specific
    input element and shows the available image for images that have
    been previously uploaded. Selecting the image will open the file
    dialog and allow for selecting a new or replacing image file.
    """
    template_name = 'oscar/forms/widgets/image_input_widget.html'

    def __init__(self, attrs=None):
        if not attrs:
            attrs = {}
        attrs['accept'] = 'image/*'
        super().__init__(attrs=attrs)

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)

        ctx['image_url'] = ''
        if value and not isinstance(value, InMemoryUploadedFile):
            # can't display images that aren't stored - pass empty string to context
            ctx['image_url'] = value

        ctx['image_id'] = "%s-image" % ctx['widget']['attrs']['id']
        return ctx


class WYSIWYGTextArea(forms.Textarea):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('class', '')
        kwargs['attrs']['class'] += ' wysiwyg'
        super().__init__(*args, **kwargs)


def datetime_format_to_js_date_format(format):
    """
    Convert a Python datetime format to a date format suitable for use with
    the JS date picker we use.
    """
    format = format.split()[0]
    return datetime_format_to_js_datetime_format(format)


def datetime_format_to_js_time_format(format):
    """
    Convert a Python datetime format to a time format suitable for use with the
    JS time picker we use.
    """
    try:
        format = format.split()[1]
    except IndexError:
        pass
    converted = format
    replacements = {
        '%H': 'hh',
        '%I': 'HH',
        '%M': 'ii',
        '%S': 'ss',
    }
    for search, replace in replacements.items():
        converted = converted.replace(search, replace)
    return converted.strip()


def datetime_format_to_js_datetime_format(format):
    """
    Convert a Python datetime format to a time format suitable for use with
    the datetime picker we use, http://www.malot.fr/bootstrap-datetimepicker/.
    """
    converted = format
    replacements = {
        '%Y': 'yyyy',
        '%y': 'yy',
        '%m': 'mm',
        '%d': 'dd',
        '%H': 'hh',
        '%I': 'HH',
        '%M': 'ii',
        '%S': 'ss',
    }
    for search, replace in replacements.items():
        converted = converted.replace(search, replace)

    return converted.strip()


def datetime_format_to_js_input_mask(format):
    # taken from
    # http://stackoverflow.com/questions/15175142/how-can-i-do-multiple-substitutions-using-regex-in-python  # noqa
    def multiple_replace(dict, text):
        # Create a regular expression  from the dictionary keys
        regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

        # For each match, look-up corresponding value in dictionary
        return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text)

    replacements = {
        '%Y': 'yyyy',
        '%y': 'yy',
        '%m': 'mm',
        '%d': 'dd',
        '%H': 'HH',
        '%I': 'hh',
        '%M': 'MM',
        '%S': 'ss',
    }
    return multiple_replace(replacements, format).strip()


class DateTimeWidgetMixin(object):

    template_name = 'oscar/forms/widgets/date_time_picker.html'

    def get_format(self):
        return self.format or formats.get_format(self.format_key)[0]

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['data-inputmask'] = "'alias': 'datetime', 'inputFormat': '{mask}'".format(
            mask=datetime_format_to_js_input_mask(self.get_format()))
        return attrs


class TimePickerInput(DateTimeWidgetMixin, forms.TimeInput):
    """
    A widget that passes the date format to the JS date picker in a data
    attribute.
    """
    format_key = 'TIME_INPUT_FORMATS'

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        ctx['div_attrs'] = {
            'data-oscarWidget': 'time',
            'data-timeFormat': datetime_format_to_js_time_format(self.get_format()),
        }
        ctx['icon_classes'] = 'icon-time glyphicon-time'
        return ctx


class DatePickerInput(DateTimeWidgetMixin, forms.DateInput):
    """
    A widget that passes the date format to the JS date picker in a data
    attribute.
    """
    format_key = 'DATE_INPUT_FORMATS'

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        ctx['div_attrs'] = {
            'data-oscarWidget': 'date',
            'data-dateFormat': datetime_format_to_js_date_format(self.get_format()),
        }
        ctx['icon_classes'] = 'icon-calendar glyphicon-calendar'
        return ctx


class DateTimePickerInput(DateTimeWidgetMixin, forms.DateTimeInput):
    """
    A widget that passes the datetime format to the JS datetime picker in a
    data attribute.

    It also removes seconds by default. However this only works with widgets
    without localize=True.

    For localized widgets refer to
    https://docs.djangoproject.com/en/1.11/topics/i18n/formatting/#creating-custom-format-files # noqa
    instead to override the format.
    """
    format_key = 'DATETIME_INPUT_FORMATS'

    def __init__(self, *args, **kwargs):
        include_seconds = kwargs.pop('include_seconds', False)
        super().__init__(*args, **kwargs)

        if not include_seconds and self.format:
            self.format = re.sub(':?%S', '', self.format)

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        ctx['div_attrs'] = {
            'data-oscarWidget': 'datetime',
            'data-datetimeFormat': datetime_format_to_js_datetime_format(self.get_format()),
        }
        ctx['icon_classes'] = 'icon-calendar glyphicon-calendar'
        return ctx


class AdvancedSelect(forms.Select):
    """
    Customised Select widget that allows a list of disabled values to be passed
    to the constructor.  Django's default Select widget doesn't allow this so
    we have to override the render_option method and add a section that checks
    for whether the widget is disabled.
    """

    def __init__(self, attrs=None, choices=(), disabled_values=()):
        self.disabled_values = set(force_text(v) for v in disabled_values)
        super().__init__(attrs, choices)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if force_text(value) in self.disabled_values:
            option['attrs']['disabled'] = True
        return option


class RemoteSelect(forms.Select):
    """
    Somewhat reusable widget that allows AJAX lookups in combination with
    select2.
    Requires setting the URL of a lookup view either as class attribute or when
    constructing
    """
    lookup_url = None

    def __init__(self, *args, **kwargs):
        self.lookup_url = kwargs.pop('lookup_url', self.lookup_url)
        if self.lookup_url is None:
            raise ValueError("RemoteSelect requires a lookup URL")

        super().__init__(*args, **kwargs)

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.update({
            'data-ajax-url': self.lookup_url,
            'data-multiple': 'multiple' if self.allow_multiple_selected else '',
            'data-required': 'required' if self.is_required else '',
        })
        return attrs

    def optgroups(self, name, value, attrs=None):
        """
        Borrowed liberally from https://github.com/applegrew/django-select2

        For model choice fields, return only the selected options. The rest
        will be populated with AJAX.
        """

        default = (None, [], 0)
        groups = [default]
        has_selected = False
        selected_choices = {force_text(v) for v in value}
        if not self.is_required and not self.allow_multiple_selected:
            default[1].append(self.create_option(name, '', '', False, 0))

        # If thi is not a model choice field then just return all choices
        if not isinstance(self.choices, ModelChoiceIterator):
            return super().optgroups(name, value, attrs=attrs)

        selected_choices = {
            c for c in selected_choices if c not in self.choices.field.empty_values
        }
        choices = (
            (obj.pk, force_text(obj))
            for obj in self.choices.queryset.filter(pk__in=selected_choices)
        )
        for option_value, option_label in choices:
            selected = (
                str(option_value) in value
                and (has_selected is False or self.allow_multiple_selected)
            )
            if selected is True and has_selected is False:
                has_selected = True
            index = len(default[1])
            subgroup = default[1]
            subgroup.append(
                self.create_option(name, option_value, option_label, selected_choices, index))

        return groups


class MultipleRemoteSelect(RemoteSelect):
    allow_multiple_selected = True
