import keyword

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model


class ExtendedURLValidator(validators.URLValidator):

    def __init__(self, *args, **kwargs):
        self.is_local_url = False
        super(ExtendedURLValidator, self).__init__(*args, **kwargs)

    def __call__(self, value):
        try:
            super(ExtendedURLValidator, self).__call__(value)
        except ValidationError:
            # The parent validator will raise an exception if the URL is not a
            # valid absolute URL so we test here to see if it is a local URL.
            if value:
                self.validate_local_url(value)
            else:
                raise

    def validate_local_url(self, value):
        value = self.clean_url(value)
        try:
            resolve(value)
        except Http404:
            # We load flatpages here as it causes a circular reference problem
            # sometimes.  FlatPages is None if not installed
            FlatPage = get_model('flatpages', 'FlatPage')
            if FlatPage is not None:
                try:
                    FlatPage.objects.get(url=value)
                except FlatPage.DoesNotExist:
                    self.is_local_url = True
                else:
                    return
            raise ValidationError(_('The URL "%s" does not exist') % value)
        else:
            self.is_local_url = True

    def clean_url(self, value):
        """
        Ensure url has a preceding slash and no query string
        """
        if value != '/':
            value = '/' + value.lstrip('/')
        q_index = value.find('?')
        if q_index > 0:
            value = value[:q_index]
        return value


class URLDoesNotExistValidator(ExtendedURLValidator):

    def __call__(self, value):
        """
        Validate that the URL does not already exist.

        The URL will be verified first and raises ``ValidationError`` when
        it is invalid. A valid URL is checked for existence and raises
        ``ValidationError`` if the URL already exists.

        This validation uses two calls to ExtendedURLValidator which can
        be slow. Be aware of this, when you use it.

        Returns ``None`` if URL is valid and does not exist.
        """
        try:
            self.validate_local_url(value)
        except ValidationError:
            # Page exists - that is what we want
            return
        raise ValidationError(
            _('Specified page already exists!'), code='invalid')


def non_whitespace(value):
    stripped = value.strip()
    if not stripped:
        raise ValidationError(
            _("This field is required"))
    return stripped


def non_python_keyword(value):
    if keyword.iskeyword(value):
        raise ValidationError(
            _("This field is invalid as its value is forbidden")
        )
    return value


class CommonPasswordValidator(validators.BaseValidator):

    forbidden_passwords = [
        'password',
        '1234',
        '12345'
        '123456',
        '123456y',
        '123456789',
        'iloveyou',
        'princess',
        'monkey',
        'rockyou',
        'babygirl',
        'monkey',
        'qwerty',
        '654321',
        'dragon',
        'pussy',
        'baseball',
        'football',
        'letmein',
        'monkey',
        '696969',
        'abc123',
        'qwe123',
        'qweasd',
        'mustang',
        'michael',
        'shadow',
        'master',
        'jennifer',
        '111111',
        '2000',
        'jordan',
        'superman'
        'harley'
    ]
    message = _("Please choose a less common password")
    code = 'password'

    def __init__(self, password_file=None):
        self.limit_value = password_file

    def clean(self, value):
        return value.strip()

    def compare(self, value, limit):
        return value in self.forbidden_passwords

    def get_forbidden_passwords(self):
        if self.limit_value is None:
            return self.forbidden_passwords


# Shim for backwards compatibility with Django 1.8. This can be removed when
# support for Django 1.8 is dropped.
def validate_password(password, user=None):
    try:
        # Django 1.9 and above
        from django.contrib.auth import password_validation
        # If AUTH_PASSWORD_VALIDATORS is empty, then supply validators
        # equivalent to what Oscar used to do itself (deprecated).
        if settings.AUTH_PASSWORD_VALIDATORS:
            password_validators = None
        else:
            password_validators = [
                password_validation.MinimumLengthValidator(min_length=6),
                password_validation.CommonPasswordValidator(),
            ]
        return password_validation.validate_password(
            password, user=user, password_validators=password_validators)
    except ImportError:
        # Django 1.8 - use our custom validators. Note that these are Field
        # validators and have a different signature to the password validators
        # used above.
        password_validators = [
            validators.MinLengthValidator(6),
            CommonPasswordValidator(),
        ]

        errors = []
        for validator in password_validators:
            try:
                validator(password)
            except ValidationError as error:
                errors.append(error)

        if errors:
            raise ValidationError(errors)
