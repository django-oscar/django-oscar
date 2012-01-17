from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.http import Http404
from django.utils.translation import ugettext_lazy as _


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
            raise ValidationError(_('Specified page does not exist'))

    def fix_local_url(self, value):
        """
        Puts preceding and trailing slashes to local URL name
        """
        if value != '/':
            value = '/' + value.lstrip('/')
        return value
