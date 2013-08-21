from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import CharField, DecimalField
from django.db.models import SubfieldBase
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
    add_introspection_rules([], [
        "^oscar\.models\.fields\.UppercaseCharField$"])
    add_introspection_rules([], [
        "^oscar\.models\.fields\.NullCharField$"])


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


class UppercaseCharField(CharField):
    def to_python(self, value):
        return super(UppercaseCharField, self).to_python(value).upper()


class NullCharField(CharField):
    """
    CharField that stores '' as None and returns None as ''
    Useful when using unique=True and forms. Implies null==blank==True.

    When a ModelForm with a CharField with null=True gets saved, the field will
    be set to '': https://code.djangoproject.com/ticket/9590
    This breaks usage with unique=True, as '' is considered equal to another
    field set to ''.
    """
    description = "CharField that stores '' as None and returns None as ''"

    # necessary for to_python to be called
    __metaclass__ = SubfieldBase

    def __init__(self, *args, **kwargs):
        if not kwargs.get('null', True) or not kwargs.get('blank', True):
            raise ImproperlyConfigured(
                "NullCharField implies null==blank==True")
        kwargs['null'] = kwargs['blank'] = True
        super(NullCharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, CharField):
            return value
        if value is None:
            return u""
        else:
            return value

    def get_prep_value(self, value):
        prepped = super(NullCharField, self).get_prep_value(value)
        if prepped == "":
            return None
        else:
            return prepped
