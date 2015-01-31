
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import CharField, DecimalField, Field
from django.db.models import SubfieldBase
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxLengthValidator

from oscar.core import validators
from oscar.forms import fields

import oscar.core.phonenumber as phonenumber
# allow importing as oscar.models.fields.AutoSlugField
from .autoslugfield import AutoSlugField
AutoSlugField = AutoSlugField

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
    add_introspection_rules([], [
        "^oscar\.models\.fields\.PhoneNumberField$"])
    add_introspection_rules([], [
        "^oscar\.models\.fields\.AutoSlugField$"])


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

    def deconstruct(self):
        """
        deconstruct() is needed by Django's migration framework
        """
        name, path, args, kwargs = super(ExtendedURLField, self).deconstruct()
        # Add verify_exists to kwargs if it's not the default value.
        if self.verify_exists is not None:
            kwargs['verify_exists'] = self.verify_exists
        # We have a default value for max_length; remove it in that case
        if self.max_length == 200:
            del kwargs['max_length']
        return name, path, args, kwargs


class PositiveDecimalField(DecimalField):
    """
    A simple subclass of ``django.db.models.fields.DecimalField`` that
    restricts values to be non-negative.
    """
    def formfield(self, **kwargs):
        return super(PositiveDecimalField, self).formfield(min_value=0)


class UppercaseCharField(six.with_metaclass(SubfieldBase, CharField)):
    """
    A simple subclass of ``django.db.models.fields.CharField`` that
    restricts all text to be uppercase.

    Defined with the with_metaclass helper so that to_python is called
    https://docs.djangoproject.com/en/1.6/howto/custom-model-fields/#the-subfieldbase-metaclass  # NOQA
    """

    def to_python(self, value):
        val = super(UppercaseCharField, self).to_python(value)
        if isinstance(val, six.string_types):
            return val.upper()
        else:
            return val


class NullCharField(six.with_metaclass(SubfieldBase, CharField)):
    """
    CharField that stores '' as None and returns None as ''
    Useful when using unique=True and forms. Implies null==blank==True.

    When a ModelForm with a CharField with null=True gets saved, the field will
    be set to '': https://code.djangoproject.com/ticket/9590
    This breaks usage with unique=True, as '' is considered equal to another
    field set to ''.
    """
    description = "CharField that stores '' as None and returns None as ''"

    def __init__(self, *args, **kwargs):
        if not kwargs.get('null', True) or not kwargs.get('blank', True):
            raise ImproperlyConfigured(
                "NullCharField implies null==blank==True")
        kwargs['null'] = kwargs['blank'] = True
        super(NullCharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        val = super(NullCharField, self).to_python(value)
        return val if val is not None else u''

    def get_prep_value(self, value):
        prepped = super(NullCharField, self).get_prep_value(value)
        return prepped if prepped != u"" else None

    def deconstruct(self):
        """
        deconstruct() is needed by Django's migration framework
        """
        name, path, args, kwargs = super(NullCharField, self).deconstruct()
        del kwargs['null']
        del kwargs['blank']
        return name, path, args, kwargs


class PhoneNumberField(six.with_metaclass(SubfieldBase, CharField)):
    """
    An international phone number.

    * Validates a wide range of phone number formats
    * Displays it nicely formatted

    Notes
    -----
    This field is based on work in django-phonenumber-field
    https://github.com/maikhoepfel/django-phonenumber-field/

    See ``oscar/core/phonenumber.py`` for the relevant copyright and
    permission notice.
    """

    default_validators = [phonenumber.validate_international_phonenumber]

    description = _("Phone number")

    def __init__(self, *args, **kwargs):
        # There's no useful distinction between '' and None for a phone
        # number. To avoid running into issues that are similar to what
        # NullCharField tries to solve, we just forbid settings null=True.
        if kwargs.get('null', False):
            raise ImproperlyConfigured(
                "null=True is not supported on PhoneNumberField")
        # Set a default max_length.
        kwargs['max_length'] = kwargs.get('max_length', 128)
        super(PhoneNumberField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """
        Returns field's value prepared for saving into a database.
        """
        value = phonenumber.to_python(value)
        if value is None:
            return u''
        return value.as_e164 if value.is_valid() else value.raw_input

    def to_python(self, value):
        return phonenumber.to_python(value)

    def value_to_string(self, obj):
        """
        Used when the field is serialized. See Django docs.
        """
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    def deconstruct(self):
        """
        deconstruct() is needed by Django's migration framework.
        """
        name, path, args, kwargs = super(PhoneNumberField, self).deconstruct()
        # Delete kwargs at default value.
        if self.max_length == 128:
            del kwargs['max_length']
        return name, path, args, kwargs
