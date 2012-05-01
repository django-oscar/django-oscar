from django.test import TestCase
from django.core.exceptions import ValidationError
from django.conf import settings

from django.contrib.flatpages.models import FlatPage

from oscar.core.loading import import_module, AppNotFoundError, \
        get_classes, get_class, ClassNotFoundError
from oscar.core.validators import ExtendedURLValidator
from oscar.core.validators import URLDoesNotExistValidator
from oscar.test import patch_settings


class ImportAppTests(TestCase):

    def test_a_specified_class_is_imported_correctly(self):
        module = import_module('analytics.models', ['ProductRecord'])
        self.assertEqual('oscar.apps.analytics.models', module.__name__)

    def test_unknown_apps_raise_exception(self):
        self.assertRaises(AppNotFoundError, import_module, 'banana', ['skin'])


class ClassLoadingTests(TestCase):

    def test_loading_oscar_classes(self):
        Product, Category = get_classes('catalogue.models', ('Product', 'Category'))
        self.assertEqual('oscar.apps.catalogue.models', Product.__module__)
        self.assertEqual('oscar.apps.catalogue.models', Category.__module__)

    def test_loading_oscar_class(self):
        Product = get_class('catalogue.models', 'Product')
        self.assertEqual('oscar.apps.catalogue.models', Product.__module__)

    def test_loading_oscar_class_from_dashboard_subapp(self):
        ReportForm = get_class('dashboard.reports.forms', 'ReportForm')
        self.assertEqual('oscar.apps.dashboard.reports.forms', ReportForm.__module__)

    def test_bad_appname_raises_exception(self):
        with self.assertRaises(AppNotFoundError):
            get_classes('fridge.models', ('Product', 'Category'))

    def test_bad_classname_raises_exception(self):
        with self.assertRaises(ClassNotFoundError):
            get_class('catalogue.models', 'Monkey')


class ClassLoadingWithLocalOverrideTests(TestCase):

    def setUp(self):
        self.installed_apps = list(settings.INSTALLED_APPS)
        self.installed_apps[self.installed_apps.index('oscar.apps.shipping')] = 'tests.shipping'

    def test_loading_class_defined_in_local_module(self):
        with patch_settings(INSTALLED_APPS=self.installed_apps):
            (Free,) = get_classes('shipping.methods', ('Free',))
            self.assertEqual('tests.shipping.methods', Free.__module__)

    def test_loading_class_which_is_not_defined_in_local_module(self):
        with patch_settings(INSTALLED_APPS=self.installed_apps):
            (FixedPrice,) = get_classes('shipping.methods', ('FixedPrice',))
            self.assertEqual('oscar.apps.shipping.methods', FixedPrice.__module__)

    def test_loading_class_from_module_not_defined_in_local_app(self):
        with patch_settings(INSTALLED_APPS=self.installed_apps):
            (Repository,) = get_classes('shipping.repository', ('Repository',))
            self.assertEqual('oscar.apps.shipping.repository', Repository.__module__)

    def test_loading_classes_defined_in_both_local_and_oscar_modules(self):
        with patch_settings(INSTALLED_APPS=self.installed_apps):
            (Free, FixedPrice) = get_classes('shipping.methods', ('Free', 'FixedPrice'))
            self.assertEqual('tests.shipping.methods', Free.__module__)
            self.assertEqual('oscar.apps.shipping.methods', FixedPrice.__module__)


class ValidatorTests(TestCase):

    def test_validate_local_url(self):
        v = ExtendedURLValidator(verify_exists=True)

        try:
            v('/')
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError'
                      'unexpectedly!')

        try:
            v('/?q=test')  # Query strings shouldn't affect validation
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError'
                      'unexpectedly!')

        with self.assertRaises(ValidationError):
            v('/invalid/')

        with self.assertRaises(ValidationError):
            v('/invalid/?q=test')  # Query strings shouldn't affect validation

        try:
            v('products/')
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError'
                      'unexpectedly!')

        with self.assertRaises(ValidationError):
            v('/products')  # Missing the / is bad

        FlatPage(title='test page', url='/test/page/').save()
        try:
            v('/test/page/')
        except ValidationError:
            self.fail('ExtendedURLValidator raises ValidationError'
                      'unexpectedly!')

    def test_validate_url_does_not_exist(self):
        validator = URLDoesNotExistValidator()
        self.assertRaises(ValidationError, validator, '/')
        try:
            validator('/invalid/')
        except ValidationError:
            self.fail('URLDoesNotExistValidator raised ValidationError'
                      'unexpectedly!')

        FlatPage(title='test page', url='/test/page/').save()
        self.assertRaises(ValidationError, validator, '/test/page/')


class ClassLoadingWithLocalOverrideWith3SegmentsTests(TestCase):

    def setUp(self):
        self.installed_apps = list(settings.INSTALLED_APPS)
        self.installed_apps[self.installed_apps.index('oscar.apps.shipping')] = 'tests.apps.shipping'

    def test_loading_class_defined_in_local_module(self):
        with patch_settings(INSTALLED_APPS=self.installed_apps):
            (Free,) = get_classes('shipping.methods', ('Free',))
            self.assertEqual('tests.apps.shipping.methods', Free.__module__)
