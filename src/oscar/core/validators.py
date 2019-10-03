import keyword

from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.core import validators
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import get_urlconf, resolve
from django.utils.translation import get_language, get_language_from_path
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from oscar.core.loading import get_model


class ExtendedURLValidator(validators.URLValidator):

    def __init__(self, *args, **kwargs):
        self.is_local_url = False
        super().__init__(*args, **kwargs)

    def __call__(self, value):
        try:
            super().__call__(value)
        except ValidationError:
            # The parent validator will raise an exception if the URL is not a
            # valid absolute URL so we test here to see if it is a local URL.
            if value:
                self.validate_local_url(value)
            else:
                raise

    def _validate_url(self, value):
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

    def validate_local_url(self, value):
        value = self.clean_url(value)
        # If we have i18n pattern in the URLconf, by default it will be
        # resolved against default language by `LocaleRegexURLResolver`. In
        # this case, it won't resolve the path /de/catalogue/ when default
        # language code is "en-gb" and so that path validation won't pass,
        # which is incorrect. In order to work it around, we extract language
        # code from URL and override current locale within the locale prefix of
        # the URL.
        urlconf = get_urlconf()
        i18n_patterns_used, _ = is_language_prefix_patterns_used(urlconf)
        redefined_language = None
        if i18n_patterns_used:
            language = get_language_from_path(value)
            current_language = get_language()
            if language != current_language:
                redefined_language = language
        if redefined_language:
            with override(redefined_language):
                self._validate_url(value)
        else:
            self._validate_url(value)

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
