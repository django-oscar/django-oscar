from django.forms import fields
from django.core.validators import URL_VALIDATOR_USER_AGENT
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from oscar.forms.widgets import InfiniteChoiceWidget

from oscar.core import validators


class ExtendedURLField(fields.URLField):
    """
    Custom field similar to URLField type field, however also accepting and
    validating local relative URLs, ie. '/product/'
    """

    def __init__(self, max_length=None, min_length=None, verify_exists=False,
            validator_user_agent=URL_VALIDATOR_USER_AGENT, *args, **kwargs):
        # intentionally skip one step when calling super()
        super(fields.URLField, self).__init__(max_length, min_length, *args,
                                              **kwargs)
        validator = validators.ExtendedURLValidator(
            verify_exists=verify_exists,
            validator_user_agent=validator_user_agent)
        self.validators.append(validator)

    def to_python(self, value):
        # We need to avoid having 'http' inserted at the start of
        # every value
        if value and value.startswith('/'):
            return value
        return super(ExtendedURLField, self).to_python(value)


class InfiniteChoiceField(fields.Field):
    '''
    Infinite choice field
    '''

    default_error_messages = {
        'invalid_choice': _(u'Select a valid choice. %(value)s is not one of the available choices.'),
    }

    def __init__(self, data_model, autocomplete_url, multiple=None, widget_attrs=None, **kwargs):
        self.data_model = data_model
        self.multiple = multiple
        widget = InfiniteChoiceWidget(autocomplete_url, multiple, widget_attrs, **kwargs)
        super(InfiniteChoiceField, self).__init__(widget=widget, **kwargs)

    def to_python(self, value):
        empty_values = validators.validators.EMPTY_VALUES + (u'None', 'None')
        if value in empty_values:
            return None
        if self.multiple:
            values = value.split(',')
            qs = self.data_model.objects.filter(pk__in=values)
            pks = set([i.pk for i in qs])
            for val in values:
                if not int(val) in pks:
                    raise ValidationError(self.error_messages['invalid_choice'] % {'value': val})
            return qs
        else:
            try:
                return self.data_model.objects.get(pk=value)
            except self.data_model.DoesNotExist:
                raise ValidationError(self.error_messages['invalid_choice'] % {'value': value})

    def prepare_value(self, value):
        if value is not None and hasattr(value, '__iter__') and self.multiple:
            return u','.join(unicode(v.pk) for v in value)
        return unicode(value)
