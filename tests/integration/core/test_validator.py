import unittest

import django
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.contrib.flatpages.models import FlatPage

from oscar.core.validators import (
    ExtendedURLValidator, URLDoesNotExistValidator, validate_password)


class TestExtendedURLValidator(TestCase):

    def setUp(self):
        self.validator = ExtendedURLValidator()

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


class TestURLDoesNotExistValidator(TestCase):

    def setUp(self):
        self.validator = URLDoesNotExistValidator()

    def test_raises_exception_for_local_urls(self):
        self.assertRaises(ValidationError, self.validator, '/')

    def test_raises_exception_for_flatpages(self):
        FlatPage.objects.create(title='test page', url='/test/page/')
        self.assertRaises(ValidationError, self.validator, '/test/page/')


class TestPasswordValidator(TestCase):

    @unittest.skipUnless(django.VERSION < (1, 9), 'Django 1.8 only')
    def test_validator_fallback_django_18(self):
        # In Django 1.8, we use our custom validators
        with self.assertRaises(ValidationError):
            # Should be in the list of common passwords
            validate_password('password')

        with self.assertRaises(ValidationError):
            # Should be too short (min is 6 characters)
            validate_password('short')

        # This should validate
        self.assertIsNone(validate_password('zNWJKpyq7idw'))

    @unittest.skipUnless(django.VERSION >= (1, 9), 'Django 1.9 and up only')
    def test_validator_uses_auth_validators(self):
        with self.assertRaises(ValidationError):
            # Should be in the list of common passwords
            validate_password('password')

        with self.assertRaises(ValidationError):
            # Should be too short (min is 6 characters)
            validate_password('short')

        with self.assertRaises(ValidationError):
            # Numeric passwords not allowed
            validate_password('9796474332')

        # This should validate
        self.assertIsNone(validate_password('zNWJKpyq7idw'))

    @unittest.skipUnless(django.VERSION >= (1, 9), 'Django 1.9 and up only')
    @override_settings(AUTH_PASSWORD_VALIDATORS=[])
    def test_validator_fallback_if_auth_setting_empty(self):
        # If AUTH_PASSWORD_VALIDATORS we should still enforce validation
        # consistent with previous versions of Oscar.
        with self.assertRaises(ValidationError):
            # Should be too short (min is 6 characters)
            validate_password('short')
