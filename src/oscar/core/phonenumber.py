# This module is based on django-phone-number-field
# https://github.com/stefanfoulis/django-phonenumber-field
#
# Here is the relevant copyright and permissions notice.
#
# Copyright (c) 2011 Stefan Foulis and contributors.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import phonenumbers
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class PhoneNumber(phonenumbers.phonenumber.PhoneNumber):
    """
    A extended version of phonenumbers.phonenumber.PhoneNumber that provides
    some neat and more pythonic, easy to access methods. This makes using a
    PhoneNumber instance much easier, especially in templates and such.
    """
    format_map = {
        'E164': phonenumbers.PhoneNumberFormat.E164,
        'INTERNATIONAL': phonenumbers.PhoneNumberFormat.INTERNATIONAL,
        'NATIONAL': phonenumbers.PhoneNumberFormat.NATIONAL,
        'RFC3966': phonenumbers.PhoneNumberFormat.RFC3966,
    }

    @classmethod
    def from_string(cls, phone_number, region=None):
        phone_number_obj = cls()
        if region is None:
            region = getattr(settings, 'PHONENUMBER_DEFAULT_REGION', None)
        phonenumbers.parse(number=phone_number, region=region,
                           keep_raw_input=True, numobj=phone_number_obj)
        return phone_number_obj

    def __str__(self):
        format_string = getattr(
            settings, 'PHONENUMBER_DEFAULT_FORMAT', 'INTERNATIONAL')
        fmt = self.format_map[format_string]
        if self.is_valid():
            return self.format_as(fmt)
        return self.raw_input

    def is_valid(self):
        """
        checks whether the number supplied is actually valid
        """
        return phonenumbers.is_valid_number(self)

    def format_as(self, format):
        if self.is_valid():
            return phonenumbers.format_number(self, format)
        else:
            return self.raw_input

    @property
    def as_international(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    @property
    def as_e164(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.E164)

    @property
    def as_national(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.NATIONAL)

    @property
    def as_rfc3966(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.RFC3966)

    def __len__(self):
        return len(six.text_type(self))

    def __eq__(self, other):
        if type(other) == PhoneNumber:
            return self.as_e164 == other.as_e164
        else:
            return super(PhoneNumber, self).__eq__(other)


def to_python(value):
    if value in validators.EMPTY_VALUES:  # None or ''
        phone_number = None
    elif value and isinstance(value, six.string_types):
        try:
            phone_number = PhoneNumber.from_string(phone_number=value)
        except phonenumbers.phonenumberutil.NumberParseException:
            # the string provided is not a valid PhoneNumber.
            phone_number = PhoneNumber(raw_input=value)
    elif isinstance(value, PhoneNumber):
        phone_number = value
    return phone_number


def validate_international_phonenumber(value):
    phone_number = to_python(value)
    if phone_number and not phone_number.is_valid():
        raise ValidationError(_(u'The phone number entered is not valid.'))
