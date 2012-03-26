import re

from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from django.db.models import get_model

class ExtendedURLValidator(validators.URLValidator):
    def __call__(self, value):
        try:
            super(ExtendedURLValidator, self).__call__(value)
        except ValidationError:
            if value:
                self.validate_local_url(value)
            else:
                raise

    def validate_local_url(self, value):
        """
        Validate local URL name
        """
        try:
            value = self.fix_local_url(value)
            if self.verify_exists:
                resolve(value)
            self.is_local_url = True
        except Http404:
            # We load flatpages here as it causes a circular reference problem
            # sometimes.  FlatPages is None if not installed
            FlatPage = get_model('flatpages', 'FlatPage')
            if FlatPage is not None:
                for page in FlatPage.objects.all().only(('url')):
                    if value == page.url:
                        return
            raise ValidationError(_('Specified page does not exist'))

    def fix_local_url(self, value):
        """
        Puts preceding and trailing slashes to local URL name
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
