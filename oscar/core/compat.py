from django.utils import six

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from oscar.core.loading import get_model


# A setting that can be used in foreign key declarations
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
# Two additional settings that are useful in South migrations when
# specifying the user model in the FakeORM
try:
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME = AUTH_USER_MODEL.rsplit('.', 1)
except ValueError:
    raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form"
                               " 'app_label.model_name'")


def get_user_model():
    """
    Return the User model. Doesn't require the app cache to be fully
    initialised.

    This used to live in compat to support both Django 1.4's fixed User model
    and custom user models introduced thereafter.
    Support for Django 1.4 has since been dropped in Oscar, but our
    get_user_model remains because code relies on us annotating the _meta class
    with the additional fields, and other code might rely on it as well.
    """

    try:
        model = get_model(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME)
    except LookupError:
        # Convert exception to an ImproperlyConfigured exception for
        # backwards compatibility with previous Oscar versions and the
        # original get_user_model method in Django.
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL refers to model '%s' that has not been installed"
            % settings.AUTH_USER_MODEL)

    # Test if user model has any custom fields and add attributes to the _meta
    # class
    core_fields = set([f.name for f in User._meta.fields])
    model_fields = set([f.name for f in model._meta.fields])
    new_fields = model_fields.difference(core_fields)
    model._meta.has_additional_fields = len(new_fields) > 0
    model._meta.additional_fields = new_fields

    return model


def existing_user_fields(fields):
    """
    Starting with Django 1.6, the User model can be overridden  and it is no
    longer safe to assume the User model has certain fields. This helper
    function assists in writing portable forms Meta.fields definitions
    when those contain fields on the User model

    Usage:
    class UserForm(forms.Form):
        ...
        class Meta:
            # won't break if first_name is not defined on User model
            fields = existing_user_fields(['first_name', 'last_name'])
    """
    user_fields = get_user_model()._meta.fields
    user_field_names = [field.name for field in user_fields]
    return list(set(fields) & set(user_field_names))


# Python3 compatibility layer


# Make backwards-compatible atomic decorator available
try:
    from django.db.transaction import atomic as atomic_compat
except ImportError:
    from django.db.transaction import commit_on_success as atomic_compat
atomic_compat = atomic_compat

"""
Unicode compatible wrapper for CSV reader and writer that abstracts away
differences between Python 2 and 3. A package like unicodecsv would be
preferable, but it's not Python 3 compatible yet.

Code from http://python3porting.com/problems.html
Changes:
- Classes renamed to include CSV.
- Unused 'codecs' import is dropped.
- Added possibility to specify an open file to the writer to send as response
  of a view
"""

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
    """
    Python 2 and 3 compatible CSV writer. Supports two modes:
    * Writing to an open file or file-like object:
      writer = UnicodeCSVWriter(open_file=your_file)
      ...
      your_file.close()
    * Writing to a new file:
      with UnicodeCSVWriter(filename=filename) as writer:
          ...
    """
    def __init__(self, filename=None, open_file=None, dialect=csv.excel,
                 encoding="utf-8", **kw):
        if filename is open_file is None:
            raise ImproperlyConfigured(
                "You need to specify either a filename or an open file")
        self.filename = filename
        self.f = open_file
        self.dialect = dialect
        self.encoding = encoding
        self.kw = kw
        self.writer = None

    def __enter__(self):
        assert self.filename is not None
        if PY3:
            self.f = open(self.filename, 'wt',
                          encoding=self.encoding, newline='')
        else:
            self.f = open(self.filename, 'wb')

    def __exit__(self, type, value, traceback):
        assert self.filename is not None
        if self.filename is not None:
            self.f.close()

    def writerow(self, row):
        if self.writer is None:
            self.writer = csv.writer(self.f, dialect=self.dialect, **self.kw)
        if not PY3:
            row = [six.text_type(s).encode(self.encoding) for s in row]
        self.writer.writerow(list(row))

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
