from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.db.models import get_model
from django.http import Http404
from django.utils.translation import ugettext_lazy as _


class ExtendedURLValidator(validators.URLValidator):

    def __init__(self, *args, **kwargs):
        # 'verify_exists' has been removed in Django 1.5 and so we no longer
        # pass it up to the core validator class
        self.is_local_url = False
        self.verify_exists = kwargs.pop('verify_exists', False)
        super(ExtendedURLValidator, self).__init__(*args, **kwargs)

    def __call__(self, value):
        try:
            super(ExtendedURLValidator, self).__call__(value)
        except ValidationError:
            # The parent validator will raise an exception if the URL does not
            # exist and so we test here to see if the value is a local URL.
            if self.verify_exists and value:
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
            raise ValidationError(_('Specified page does not exist'))
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
        Validate that the URL in *value* does not already exist. The
        URL will be verified first and raises ``ValidationError`` when
        it is invalid. A valid URL is checked for existance and raises
        ``ValidationError`` if the URL already exists. Setting attribute
        ``verify_exists`` has no impact on validation.
        This validation uses two calls to ExtendedURLValidator which can
        be slow. Be aware of this, when you use it.

        Returns ``None`` if URL is valid and does not exist.
        """
        self.verify_exists = False

        # calling ExtendedURLValidator twice instead of replicating its code
        # and invert the cases when a ValidationError is returned seemes to
        # be a much cleaner solution. Although this might not be the most
        # efficient way of handling this, it should have not much of an impact
        # due to its current application in flatpage creation.
        try:
            super(URLDoesNotExistValidator, self).__call__(value)
        except ValidationError:
            raise ValidationError(_('Specified page does already exist'),
                                  code='invalid')

        # check if URL exists since it seems to be valid
        try:
            self.verify_exists = True
            super(URLDoesNotExistValidator, self).__call__(value)
        except ValidationError:
            return

        raise ValidationError(_('Specified page does already exist'),
                              code='invalid')
