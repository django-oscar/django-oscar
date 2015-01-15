import re
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms.util import flatatt
from django.forms.widgets import FileInput
from django.template import Context
from django.template.loader import render_to_string
from django.utils import formats, six
from django.utils.six.moves import filter
from django.utils.six.moves import map
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import warnings

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
        '%Y': 'y',
        '%y': '99',
        '%m': 'm',
        '%d': 'd',
        '%H': 'h',
        '%I': 'h',
        '%M': 's',
        '%S': 's',
    }
    return multiple_replace(replacements, format).strip()


class DateTimeWidgetMixin(object):
    def get_format(self):
        format = self.format
        if hasattr(self, 'manual_format'):
            # For django <= 1.6.5, see
            # https://code.djangoproject.com/ticket/21173
            if self.is_localized and not self.manual_format:
                format = force_text(formats.get_format(self.format_key)[0])
        else:
            # For django >= 1.7
            format = format or formats.get_format(self.format_key)[0]

        return format

    def gett_attrs(self, attrs, format):
        if not attrs:
            attrs = {}

        attrs['data-inputmask'] = "'mask': '{mask}'".format(
            mask=datetime_format_to_js_input_mask(format))

        return attrs


class TimePickerInput(DateTimeWidgetMixin, forms.TimeInput):
    """
    A widget that passes the date format to the JS date picker in a data
    attribute.
    """
    format_key = 'TIME_INPUT_FORMATS'

    def render(self, name, value, attrs=None):
        format = self.get_format()
        input = super(TimePickerInput, self).render(
            name, value, self.gett_attrs(attrs, format))

        attrs = {'data-oscarWidget': 'time',
                 'data-timeFormat':
                 datetime_format_to_js_time_format(format),
                 }

        div = format_html('<div class="input-append date"{}>', flatatt(attrs))
        return mark_safe('{div}'
                         ' {input}'
                         ' <span class="add-on">'
                         '  <i class="icon-time"></i>'
                         ' </span>'
                         '</div>'
                         .format(div=div, input=input))


class DatePickerInput(DateTimeWidgetMixin, forms.DateInput):
    """
    A widget that passes the date format to the JS date picker in a data
    attribute.
    """
    format_key = 'DATE_INPUT_FORMATS'

    def render(self, name, value, attrs=None):
        format = self.get_format()
        input = super(DatePickerInput, self).render(
            name, value, self.gett_attrs(attrs, format))

        attrs = {'data-oscarWidget': 'date',
                 'data-dateFormat':
                 datetime_format_to_js_date_format(format),
                 }

        div = format_html('<div class="input-append date"{}>', flatatt(attrs))
        return mark_safe('{div}'
                         ' {input}'
                         ' <span class="add-on">'
                         '  <i class="icon-calendar"></i>'
                         ' </span>'
                         '</div>'
                         .format(div=div, input=input))


class DateTimePickerInput(DateTimeWidgetMixin, forms.DateTimeInput):
    """
    A widget that passes the datetime format to the JS datetime picker in a
    data attribute.

    It also removes seconds by default. However this only works with widgets
    without localize=True.

    For localized widgets refer to
    https://docs.djangoproject.com/en/1.6/topics/i18n/formatting/#creating-custom-format-files # noqa
    instead to override the format.
    """
    format_key = 'DATETIME_INPUT_FORMATS'

    def __init__(self, *args, **kwargs):
        include_seconds = kwargs.pop('include_seconds', False)
        super(DateTimePickerInput, self).__init__(*args, **kwargs)

        if not include_seconds and self.format:
            self.format = re.sub(':?%S', '', self.format)

    def render(self, name, value, attrs=None):
        format = self.get_format()
        input = super(DateTimePickerInput, self).render(
            name, value, self.gett_attrs(attrs, format))

        attrs = {'data-oscarWidget': 'datetime',
                 'data-datetimeFormat':
                 datetime_format_to_js_datetime_format(format),
                 }

        div = format_html('<div class="input-append date"{}>', flatatt(attrs))
        return mark_safe('{div}'
                         ' {input}'
                         ' <span class="add-on">'
                         '  <i class="icon-calendar"></i>'
                         ' </span>'
                         '</div>'
                         .format(div=div, input=input))


class AdvancedChoice(object):
    """
    This is a class that you can pass into an AdvancedChoiceField to disabled options.

    Some examples:

    CHOICES = (
        ('value1', 'Label 1'),
        ('value2', AdvancedChoice('Label 2', disabled=True),
        ('value3', DisabledChoice('Label 3'))
    )

    forms.ChoiceField(choices=CHOICES, widget=AdvancedSelect())
    forms.ChoiceField(choices=CHOICES, widget=AdvancedRadioSelect())
    forms.MultipleChoiceField(choices=CHOICES, widget=AdvancedSelectMultiple())
    forms.MultipleChoiceField(choices=CHOICES, widget=AdvancedCheckboxSelectMultiple())
    """

    def __init__(self, label, disabled=False):
        self.label = label
        self.disabled = disabled

    def __unicode__(self):
        return self.label


class DisabledChoice(AdvancedChoice):
    """
    This is a shortcut class for AdvancedChoice(label, disabled=True)
    """

    def __init__(self, label):
        self.label = label
        self.disabled = True


class AdvancedSelect(forms.Select):
    """
    Customised Select widget that allows a list of disabled values to be passed
    to the constructor.  Django's default Select widget doesn't allow this so
    we have to override the render_option method and add a section that checks
    for whether the widget is disabled.
    """

    def __init__(self, attrs=None, choices=(), **kwargs):

        if 'disabled_values' in kwargs:
            message = "Passing disabled_values as kwarg to AdvancedSelect is deprecated " \
                "and will be removed in the next major version of django-oscar"
            warnings.warn(message, DeprecationWarning, stacklevel=2)

        disabled_values = kwargs.pop('disabled_values', ())
        self.disabled_values = set(force_text(v) for v in disabled_values)

        super(AdvancedSelect, self).__init__(attrs, choices, **kwargs)

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_text(option_value)
        # In the next version, remove checking the option_value against self.disabled_values
        # and just rely on looking at the disabled attribute
        if getattr(option_label, 'disabled', False) or option_value in self.disabled_values:
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


class AdvancedSelectMultiple(AdvancedSelect, forms.SelectMultiple):
    pass
    # Really that simple. Python's MRO works great in this case


class AdvancedChoiceFieldRenderer(forms.widgets.ChoiceFieldRenderer):

    # Include both Bootstrap 2 & 3 classes for forwards-compatibility
    # Bootstrap 3, Bootstrap 3, Bootstrap 2
    DISABLED_CLASSES = ['disabled', 'text-muted', 'muted']
    # Bootstrap 3, Bootstrap 2
    LIST_CLASSES = ['list-unstyled', 'unstyled']

    def render(self):
        """
        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        Includes logic to apply a class to the <li> elements for appropriate styling.
        """
        # This is mostly boilerplate copied from widgets.ChoiceFieldRenderer
        # I tried to re-use the existing render method, but there wasn't a great
        # place for the ooks I needed
        id_ = self.attrs.get('id', None)
        # Includes style for both bootstrap 2.x and 3.x
        start_tag = format_html('<ul id="{0}" class="{1}">', id_, ' '.join(self.LIST_CLASSES)) if id_ else '<ul>'
        output = [start_tag]
        for i, choice in enumerate(self.choices):
            classes = [self.choice_input_class.input_type]
            choice_value, choice_label = choice

            attrs_plus = self.attrs.copy()

            # Custom code for wrapping <li> in disabled classes
            if getattr(choice_label, 'disabled', False):
                classes.extend(self.DISABLED_CLASSES)
                attrs_plus['disabled'] = 'disabled'

            if isinstance(choice_label, (tuple, list)):
                if id_:
                    attrs_plus['id'] += '_{0}'.format(i)
                sub_ul_renderer = AdvancedChoiceFieldRenderer(name=self.name,
                                                      value=self.value,
                                                      attrs=attrs_plus,
                                                      choices=choice_label)
                sub_ul_renderer.choice_input_class = self.choice_input_class

                output.append(format_html('<li class="{2}">{0}{1}</li>', choice_value,
                                          sub_ul_renderer.render(), ' '.join(classes)))
            else:
                w = self.choice_input_class(self.name, self.value,
                                            attrs_plus, choice, i)
                output.append(format_html('<li class="{1}">{0}</li>', force_text(w), ' '.join(classes)))
        output.append('</ul>')
        return mark_safe('\n'.join(output))


class AdvancedRadioFieldRenderer(AdvancedChoiceFieldRenderer):
    choice_input_class = forms.widgets.RadioChoiceInput


class AdvancedCheckboxFieldRenderer(AdvancedChoiceFieldRenderer):
    choice_input_class = forms.widgets.CheckboxChoiceInput


class AdvancedRadioSelect(forms.widgets.RendererMixin, AdvancedSelect):
    renderer = AdvancedRadioFieldRenderer
    _empty_value = ''


class AdvancedCheckboxSelectMultiple(forms.widgets.RendererMixin, AdvancedSelectMultiple):
    renderer = AdvancedCheckboxFieldRenderer
    _empty_value = []


class RemoteSelect(forms.Widget):
    """
    Somewhat reusable widget that allows AJAX lookups in combination with
    select2.
    Requires setting the URL of a lookup view either as class attribute or when
    constructing
    """
    is_multiple = False
    css = 'select2 input-xlarge'
    lookup_url = None

    def __init__(self, *args, **kwargs):
        if 'lookup_url' in kwargs:
            self.lookup_url = kwargs.pop('lookup_url')
        if self.lookup_url is None:
            raise ValueError(
                "RemoteSelect requires a lookup ULR")
        super(RemoteSelect, self).__init__(*args, **kwargs)

    def format_value(self, value):
        return six.text_type(value or '')

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        if value is None:
            return value
        else:
            return six.text_type(value)

    def render(self, name, value, attrs=None, choices=()):
        attrs = self.build_attrs(attrs, **{
            'type': 'hidden',
            'class': self.css,
            'name': name,
            'data-ajax-url': self.lookup_url,
            'data-multiple': 'multiple' if self.is_multiple else '',
            'value': self.format_value(value),
            'data-required': 'required' if self.is_required else '',
            })
        return mark_safe(u'<input %s>' % flatatt(attrs))


class MultipleRemoteSelect(RemoteSelect):
    is_multiple = True
    css = 'select2 input-xxlarge'

    def format_value(self, value):
        if value:
            return ','.join(map(six.text_type, filter(bool, value)))
        else:
            return ''

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        if value is None:
            return []
        else:
            return list(filter(bool, value.split(',')))
