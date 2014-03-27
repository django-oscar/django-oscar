from django.conf import settings
from django.contrib.auth import get_user_model as django_get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured


def get_user_model():
    """
    Return the User model.

    This used to live in compat to support both Django 1.4's fixed User model
    and custom user models introduced thereafter.
    Support for Django 1.4 has since been dropped in Oscar, but our
    get_user_model remains because code relies on us annotating the _meta class
    with the additional fields, and other code might rely on it as well.
    """
    model = django_get_user_model()

    # Test if user model has any custom fields and add attributes to the _meta
    # class
    core_fields = set([f.name for f in User._meta.fields])
    model_fields = set([f.name for f in model._meta.fields])
    new_fields = model_fields.difference(core_fields)
    model._meta.has_additional_fields = len(new_fields) > 0
    model._meta.additional_fields = new_fields

    return model


# A setting that can be used in foreign key declarations
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
# Two additional settings that are useful in South migrations when
# specifying the user model in the FakeORM
try:
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME = AUTH_USER_MODEL.rsplit('.', 1)
except ValueError:
    raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form"
                               " 'app_label.model_name'")

VALID_USER_FORM_FIELD_NAMES = set([field.name for field in User._meta.fields])


def existing_user_fields(fields):
    """
    Starting with Django 1.6, the User model can be overridden  and it is no
    longer safe to assume the User model has certain fields. This helper
    function assists in writing portable forms Meta.fields definitions
    when those contain fields on the User model
    """
    return list(set(fields) & VALID_USER_FORM_FIELD_NAMES)

#
# Python3 compatibility layer
#

try:
    import urlparse as _urlparse
except ImportError:
    from urllib import parse as _urlparse  # NOQA

urlparse = _urlparse

#
# Unicode compatible wrapper for CSV reader and writer that abstracts away
# differences between Python 2 and 3. A package like unicodecsv would be
# preferable, but it's not Python 3 compatible yet.

# Code from http://python3porting.com/problems.html
# Classes renamed to include CSV. Unused 'codecs' import is dropped.

import sys
import csv

PY3 = sys.version > '3'


class UnicodeCSVReader:
    def __init__(self, filename, dialect=csv.excel,
                 encoding="utf-8", **kw):
        self.filename = filename
        self.dialect = dialect
        self.encoding = encoding
        self.kw = kw

    def __enter__(self):
        if PY3:
            self.f = open(self.filename, 'rt',
                          encoding=self.encoding, newline='')
        else:
            self.f = open(self.filename, 'rbU')
        self.reader = csv.reader(self.f, dialect=self.dialect,
                                 **self.kw)
        return self

    def __exit__(self, type, value, traceback):
        self.f.close()

    def next(self):
        row = next(self.reader)
        if PY3:
            return row
        return [s.decode("utf-8") for s in row]

    __next__ = next

    def __iter__(self):
        return self


class UnicodeCSVWriter:
    def __init__(self, filename, dialect=csv.excel,
                 encoding="utf-8", **kw):
        self.filename = filename
        self.dialect = dialect
        self.encoding = encoding
        self.kw = kw

    def __enter__(self):
        if PY3:
            self.f = open(self.filename, 'wt',
                          encoding=self.encoding, newline='')
        else:
            self.f = open(self.filename, 'wb')
        self.writer = csv.writer(self.f, dialect=self.dialect,
                                 **self.kw)
        return self

    def __exit__(self, type, value, traceback):
        self.f.close()

    def writerow(self, row):
        if not PY3:
            row = [s.encode(self.encoding) for s in row]
        self.writer.writerow(row)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
