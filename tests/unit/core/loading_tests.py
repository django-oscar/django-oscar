from os.path import dirname
from django.test import TestCase
from django.conf import settings
from oscar.core.loading import get_model
from django.test.utils import override_settings

import oscar
from tests import temporary_python_path
from oscar.core.loading import (
    AppNotFoundError,
    get_classes, get_class, ClassNotFoundError)


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

    def test_raise_importerror_if_app_raises_importerror(self):
        installed_apps = list(settings.INSTALLED_APPS)
        installed_apps.insert(0, 'tests._site.import_error_app.catalogue')
        with override_settings(INSTALLED_APPS=installed_apps):
            with self.assertRaises(ImportError):
                get_class('catalogue.app', 'CatalogueApplication')


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
            self.installed_apps[
                self.installed_apps.index('tests._site.shipping')] = 'shipping'
            with override_settings(INSTALLED_APPS=self.installed_apps):
                (Free,) = get_classes('shipping.methods', ('Free',))
                self.assertEqual('shipping.methods', Free.__module__)

    def test_overriding_view_is_possible_without_overriding_app(self):
        from oscar.apps.customer.app import application, CustomerApplication
        # If test fails, it's helpful to know if it's caused by order of
        # execution
        self.assertEqual(CustomerApplication().summary_view.__module__,
                         'tests._site.apps.customer.views')
        self.assertEqual(application.summary_view.__module__,
                         'tests._site.apps.customer.views')


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


class TestOverridingCoreApps(TestCase):

    def test_means_the_overriding_model_is_registered_first(self):
        klass = get_model('partner', 'StockRecord')
        self.assertEqual('tests._site.apps.partner.models',
                          klass.__module__)
