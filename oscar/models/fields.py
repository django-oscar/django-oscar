from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import CharField, DecimalField, Field
from django.db.models import SubfieldBase
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.core import validators as django_validators

from oscar.core import validators
from oscar.forms import fields

import oscar.core.phonenumber as phonenumber

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
        "^oscar\.models\.fields\.PhoneNumberField$"])


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
    # necessary for to_python to be called
    __metaclass__ = SubfieldBase

    def to_python(self, value):
        val = super(UppercaseCharField, self).to_python(value)
        if isinstance(val, six.string_types):
            return val.upper()
        else:
            return val


class PhoneNumberField(Field):
    """
    Copyright (c) 2011 Stefan Foulis and contributors.
    https://github.com/stefanfoulis/django-phonenumber-field

    Taken from fork https://github.com/maikhoepfel/django-phonenumber-field/

    A international phone number field for django that uses
    http://pypi.python.org/pypi/phonenumbers for validation.

    * Validates a wide range of phone number formats
    * Displays it nicely formatted
    * Can be given a hint for the country, so that it can accept local numbers,
      that are not in an international format
    """

    attr_class = phonenumber.PhoneNumber
    descriptor_class = phonenumber.PhoneNumberDescriptor
    default_validators = [phonenumber.validate_international_phonenumber]

    description = _("Phone number")

    def __init__(self, *args, **kwargs):
        if kwargs.get('null', False):
            raise ImproperlyConfigured(
                "null=True is not supported on PhoneNumberField")
        kwargs['max_length'] = kwargs.get('max_length', 128)
        super(PhoneNumberField, self).__init__(*args, **kwargs)
        self.validators.append(django_validators.MaxLengthValidator(self.max_length))

    def get_internal_type(self):
        return "CharField"

    def get_prep_value(self, value):
        """
        Returns field's value prepared for saving into a database.
        """
        value = phonenumber.to_python(value)
        if value is None:
            return ''
        return value.as_e164 if value.is_valid() else value.raw_input

    def contribute_to_class(self, cls, name):
        super(PhoneNumberField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))
