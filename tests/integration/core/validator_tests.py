from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.flatpages.models import FlatPage

from oscar.core.validators import ExtendedURLValidator
from oscar.core.validators import URLDoesNotExistValidator


class TestExtendedURLValidatorWithVerifications(TestCase):
    """
    ExtendedURLValidator with verify_exists=True
    """

    def setUp(self):
        self.validator = ExtendedURLValidator(verify_exists=True)

    def test_validates_local_url(self):
        try:
            self.validator('/')
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError'
                      'unexpectedly!')

    def test_validates_local_url_with_query_strings(self):
        try:
            self.validator('/?q=test')  # Query strings shouldn't affect validation
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError'
                      'unexpectedly!')

    def test_raises_validation_error_for_missing_urls(self):
        with self.assertRaises(ValidationError):
            self.validator('/invalid/')

    def test_validates_urls_missing_preceding_slash(self):
        try:
            self.validator('catalogue/')
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError'
                      'unexpectedly!')

    def test_raises_validation_error_for_urls_without_trailing_slash(self):
        with self.assertRaises(ValidationError):
            self.validator('/catalogue')  # Missing the / is bad

    def test_validates_flatpages_urls(self):
        FlatPage.objects.create(title='test page', url='/test/page/')
        try:
            self.validator('/test/page/')
        except ValidationError:
            self.fail('ExtendedURLValidator raises ValidationError'
                      'unexpectedly!')


class TestExtendedURLValidatorWithoutVerifyExists(TestCase):
    """
    ExtendedURLValidator with verify_exists=False
    """

    def setUp(self):
        self.validator = URLDoesNotExistValidator()

    def test_raises_exception_for_local_urls(self):
        self.assertRaises(ValidationError, self.validator, '/')

    def test_raises_exception_for_flatpages(self):
        FlatPage.objects.create(title='test page', url='/test/page/')
        self.assertRaises(ValidationError, self.validator, '/test/page/')
