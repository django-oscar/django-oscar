from django.db.models.fields import CharField, DecimalField
from django.utils.translation import ugettext_lazy as _

from oscar.core import validators
from oscar.forms import fields

class ExtendedURLField(CharField):
    description = _("URL")

    def __init__(self, verbose_name=None, name=None, verify_exists=True, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 200)
        CharField.__init__(self, verbose_name, name, **kwargs)
        validator = validators.ExtendedURLValidator(verify_exists=verify_exists)
        self.validators.append(validator)

    def formfield(self, **kwargs):
        # As with CharField, this will cause URL validation to be performed twice
        defaults = {
            'form_class': fields.ExtendedURLField,
        }
        defaults.update(kwargs)
        return super(ExtendedURLField, self).formfield(**defaults)


class PositiveDecimalField(DecimalField):
    def formfield(self, **kwargs):
        return super(PositiveDecimalField, self).formfield(min_value=0)
