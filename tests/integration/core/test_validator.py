from django.contrib.flatpages.models import FlatPage
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils.translation import activate

from oscar.core.validators import ExtendedURLValidator, URLDoesNotExistValidator


class TestExtendedURLValidator(TestCase):
    def setUp(self):
        self.validator = ExtendedURLValidator()

    def test_validates_local_url(self):
        try:
            self.validator("/")
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")

    def test_validates_local_url_with_query_strings(self):
        try:
            self.validator("/?q=test")  # Query strings shouldn't affect validation
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")

    def test_raises_validation_error_for_missing_urls(self):
        with self.assertRaises(ValidationError):
            self.validator("/invalid/")

    def test_validates_urls_missing_preceding_slash(self):
        try:
            self.validator("catalogue/")
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")

    def test_raises_validation_error_for_urls_without_trailing_slash(self):
        with self.assertRaises(ValidationError):
            self.validator("/catalogue")  # Missing the / is bad

    def test_validates_flatpages_urls(self):
        FlatPage.objects.create(title="test page", url="/test/page/")
        try:
            self.validator("/test/page/")
        except ValidationError:
            self.fail("ExtendedURLValidator raises ValidationError unexpectedly!")


@override_settings(
    LANGUAGES=(
        ("de", "German"),
        ("en-gb", "British English"),
    )
)
class TestExtendedURLValidatorForLocalePrefixURLS(TestCase):
    def setUp(self):
        self.validator = ExtendedURLValidator()

    def test_validate_same_locals(self):
        """
        Current locale is default ("en-gb"), URL has locale prefix
        of default and current locale ("en-gb").
        """
        try:
            self.validator("/en-gb/test/")
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")

    def test_validate_prefix_locale_is_non_default(self):
        """
        Current locale is default ("en-gb"), URL has locale prefix
        of non-default locale ("de").
        """
        try:
            self.validator("/de/test/")
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")

    def test_validate_current_locale_is_non_default(self):
        """
        Current locale is non-default ("de"), URL has locale prefix
        of default locale ("en-gb").
        """
        activate("de")
        try:
            self.validator("/en-gb/test/")
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")

    def test_validate_current_and_prefix_locales_are_non_default_and_same(self):
        """
        Current locale is non-default ("de"), URL has locale prefix
        of non-default locale ("de").
        """
        activate("de")
        try:
            self.validator("/de/test/")
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")

    def test_validate_current_and_prefix_locales_are_non_default_and_different(self):
        """
        Current locale is non-default ("it"), URL has locale prefix
        of non-default locale ("de").
        """
        activate("it")
        try:
            self.validator("/de/test/")
        except ValidationError:
            self.fail("ExtendedURLValidator raised ValidationError unexpectedly!")


class TestURLDoesNotExistValidator(TestCase):
    def setUp(self):
        self.validator = URLDoesNotExistValidator()

    def test_raises_exception_for_local_urls(self):
        self.assertRaises(ValidationError, self.validator, "/")

    def test_raises_exception_for_flatpages(self):
        FlatPage.objects.create(title="test page", url="/test/page/")
        self.assertRaises(ValidationError, self.validator, "/test/page/")
