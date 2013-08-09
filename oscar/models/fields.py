from django.db.models.fields import CharField, DecimalField
from django.utils.translation import ugettext_lazy as _

from oscar.core import validators
from oscar.forms import fields

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], ["^oscar\.models\.fields\.ExtendedURLField$"])
    add_introspection_rules([], [
        "^oscar\.models\.fields\.PositiveDecimalField$"])


class ExtendedURLField(CharField):
    description = _("URL")

    def __init__(self, verbose_name=None, name=None,
                 verify_exists=None, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 200)
        CharField.__init__(self, verbose_name, name, **kwargs)
        # 'verify_exists' was deprecated in Django 1.4. To ensure backwards
        # compatibility, it is still accepted here, but only passed
        # on to the parent class if it was specified.
        self.verify_exists = verify_exists
        if verify_exists is not None:
            validator = validators.ExtendedURLValidator(
                verify_exists=verify_exists)
        else:
            validator = validators.ExtendedURLValidator()
        self.validators.append(validator)

    def formfield(self, **kwargs):
        # As with CharField, this will cause URL validation to be performed
        # twice.
        defaults = {
            'form_class': fields.ExtendedURLField,
            'verify_exists': self.verify_exists
        }
        defaults.update(kwargs)
        return super(ExtendedURLField, self).formfield(**defaults)


class PositiveDecimalField(DecimalField):
    def formfield(self, **kwargs):
        return super(PositiveDecimalField, self).formfield(min_value=0)
