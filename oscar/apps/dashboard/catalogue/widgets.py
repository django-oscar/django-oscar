import six
from django.forms.util import flatatt
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django import forms
from six.moves import filter
from six.moves import map


class ProductSelect(forms.Widget):
    is_multiple = False
    css = 'select2 input-xlarge'

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
            'data-ajax-url': reverse('dashboard:catalogue-product-lookup'),
            'data-multiple': 'multiple' if self.is_multiple else '',
            'value': self.format_value(value),
            'data-required': 'required' if self.is_required else '',
        })
        return mark_safe(u'<input %s>' % flatatt(attrs))


class ProductSelectMultiple(ProductSelect):
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
