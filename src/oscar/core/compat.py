import csv

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from oscar.core.loading import get_model

# A setting that can be used in foreign key declarations
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
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
    return [field for field in fields if field in user_field_names]


class UnicodeCSVWriter:
    """
    MS Excel compatible CSV writer. Supports two modes:
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

        if self.f:
            self.add_bom(self.f)

    def __enter__(self):
        assert self.filename is not None
        self.f = open(self.filename, 'wt', encoding=self.encoding, newline='')
        self.add_bom(self.f)
        return self

    def __exit__(self, type, value, traceback):
        assert self.filename is not None
        if self.filename is not None:
            self.f.close()

    def add_bom(self, f):
        # If encoding is UTF-8, insert a Byte Order Mark at the start of the
        # file for compatibility with MS Excel.
        if (self.encoding == 'utf-8'
                and getattr(settings, 'OSCAR_CSV_INCLUDE_BOM', False)):
            self.f.write('\ufeff')

    def writerow(self, row):
        if self.writer is None:
            self.writer = csv.writer(self.f, dialect=self.dialect, **self.kw)
        self.writer.writerow(list(row))

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
