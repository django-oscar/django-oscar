from os.path import dirname
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.test.utils import override_settings

import oscar
from oscar.core.loading import import_module, AppNotFoundError, \
        get_classes, get_class, ClassNotFoundError
from oscar.core.validators import ExtendedURLValidator
from oscar.core.validators import URLDoesNotExistValidator
from tests import temporary_python_path


class TestImportModule(TestCase):
    """
    oscar.core.loading.import_module
    """

    def test_imports_a_class_correctly(self):
        module = import_module('analytics.models', ['ProductRecord'])
        self.assertEqual('oscar.apps.analytics.models', module.__name__)

    def test_raises_exception_for_unknown_app(self):
        self.assertRaises(AppNotFoundError, import_module, 'banana', ['skin'])


class TestClassLoading(TestCase):
    """
    Oscar's class loading utilities
    """

    def test_load_oscar_classes_correctly(self):
        Product, Category = get_classes('catalogue.models', ('Product', 'Category'))
        self.assertEqual('oscar.apps.catalogue.models', Product.__module__)
        self.assertEqual('oscar.apps.catalogue.models', Category.__module__)

    def test_load_oscar_class_correctly(self):
        Product = get_class('catalogue.models', 'Product')
        self.assertEqual('oscar.apps.catalogue.models', Product.__module__)

    def test_load_oscar_class_from_dashboard_subapp(self):
        ReportForm = get_class('dashboard.reports.forms', 'ReportForm')
        self.assertEqual('oscar.apps.dashboard.reports.forms', ReportForm.__module__)

    def test_raise_exception_when_bad_appname_used(self):
        with self.assertRaises(AppNotFoundError):
            get_classes('fridge.models', ('Product', 'Category'))

    def test_raise_exception_when_bad_classname_used(self):
        with self.assertRaises(ClassNotFoundError):
            get_class('catalogue.models', 'Monkey')


class ClassLoadingWithLocalOverrideTests(TestCase):

    def setUp(self):
        self.installed_apps = list(settings.INSTALLED_APPS)
        self.installed_apps[self.installed_apps.index('oscar.apps.shipping')] = 'tests._site.shipping'

    def test_loading_class_defined_in_local_module(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Free,) = get_classes('shipping.methods', ('Free',))
            self.assertEqual('tests._site.shipping.methods', Free.__module__)

    def test_loading_class_which_is_not_defined_in_local_module(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (FixedPrice,) = get_classes('shipping.methods', ('FixedPrice',))
            self.assertEqual('oscar.apps.shipping.methods', FixedPrice.__module__)

    def test_loading_class_from_module_not_defined_in_local_app(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Repository,) = get_classes('shipping.repository', ('Repository',))
            self.assertEqual('oscar.apps.shipping.repository', Repository.__module__)

    def test_loading_classes_defined_in_both_local_and_oscar_modules(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Free, FixedPrice) = get_classes('shipping.methods', ('Free', 'FixedPrice'))
            self.assertEqual('tests._site.shipping.methods', Free.__module__)
            self.assertEqual('oscar.apps.shipping.methods', FixedPrice.__module__)

    def test_loading_classes_with_root_app(self):
        import tests._site.shipping
        path = dirname(dirname(tests._site.shipping.__file__))
        with temporary_python_path([path]):
            self.installed_apps[self.installed_apps.index('tests._site.shipping')] = 'shipping'
            with override_settings(INSTALLED_APPS=self.installed_apps):
                (Free,) = get_classes('shipping.methods', ('Free',))
                self.assertEqual('shipping.methods', Free.__module__)


class TestExtendedURLValidator(TestCase):
    """
    ExtendedURLValidator
    """

    def test_validates_local_url(self):
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
            v('catalogue/')
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError'
                      'unexpectedly!')

        with self.assertRaises(ValidationError):
            v('/catalogue')  # Missing the / is bad

        FlatPage(title='test page', url='/test/page/').save()
        try:
            v('/test/page/')
        except ValidationError:
            self.fail('ExtendedURLValidator raises ValidationError'
                      'unexpectedly!')

    def test_raises_exception_for_missing_url(self):
        validator = URLDoesNotExistValidator()
        self.assertRaises(ValidationError, validator, '/')
        try:
            validator('/invalid/')
        except ValidationError:
            self.fail('URLDoesNotExistValidator raised ValidationError'
                      'unexpectedly!')

        FlatPage(title='test page', url='/test/page/').save()
        self.assertRaises(ValidationError, validator, '/test/page/')


class ClassLoadingWithLocalOverrideWithMultipleSegmentsTests(TestCase):

    def setUp(self):
        self.installed_apps = list(settings.INSTALLED_APPS)
        self.installed_apps[self.installed_apps.index('oscar.apps.shipping')] = 'tests._site.apps.shipping'

    def test_loading_class_defined_in_local_module(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Free,) = get_classes('shipping.methods', ('Free',))
            self.assertEqual('tests._site.apps.shipping.methods', Free.__module__)


class TestGetCoreAppsFunction(TestCase):
    """
    oscar.get_core_apps function
    """

    def test_returns_core_apps_when_no_overrides_specified(self):
        apps = oscar.get_core_apps()
        self.assertEqual(oscar.OSCAR_CORE_APPS, apps)

    def test_uses_non_dashboard_override_when_specified(self):
        apps = oscar.get_core_apps(overrides=['apps.shipping'])
        self.assertTrue('apps.shipping' in apps)
        self.assertTrue('oscar.apps.shipping' not in apps)

    def test_uses_dashboard_override_when_specified(self):
        apps = oscar.get_core_apps(overrides=['apps.dashboard.catalogue'])
        self.assertTrue('apps.dashboard.catalogue' in apps)
        self.assertTrue('oscar.apps.dashboard.catalogue' not in apps)
        self.assertTrue('oscar.apps.catalogue' in apps)

