import sys
from os.path import dirname

from django.apps import apps
from django.conf import settings
from django.test import TestCase, override_settings

from oscar.core.loading import (
    AppNotFoundError,
    ClassNotFoundError,
    get_class,
    get_class_loader,
    get_classes,
    get_model,
)
from tests import temporary_python_path
from tests._site.loader import DummyClass

CustomerConfig = get_class("customer.apps", "CustomerConfig")


class TestClassLoading(TestCase):
    """
    Oscar's class loading utilities
    """

    def test_load_oscar_classes_correctly(self):
        Product, Category = get_classes("catalogue.models", ("Product", "Category"))
        self.assertEqual("oscar.apps.catalogue.models", Product.__module__)
        self.assertEqual("oscar.apps.catalogue.models", Category.__module__)

    def test_load_oscar_class_correctly(self):
        Product = get_class("catalogue.models", "Product")
        self.assertEqual("oscar.apps.catalogue.models", Product.__module__)

    def test_load_oscar_class_from_dashboard_subapp(self):
        ReportForm = get_class("dashboard.reports.forms", "ReportForm")
        self.assertEqual("oscar.apps.dashboard.reports.forms", ReportForm.__module__)

    def test_raise_exception_when_bad_appname_used(self):
        with self.assertRaises(AppNotFoundError):
            get_classes("fridge.models", ("Product", "Category"))

    def test_raise_exception_when_bad_classname_used(self):
        with self.assertRaises(ClassNotFoundError):
            get_class("catalogue.models", "Monkey")

    def test_raise_importerror_if_app_raises_importerror(self):
        """
        This tests that Oscar doesn't fall back to using the Oscar core
        app class if the overriding app class throws an ImportError.

        "get_class()" returns None in this case, since there is no such named
        class in the core app. We use this fictitious class because classes in
        the "models" and "views" modules (along with modules they are related
        to) are imported as part of the Django app-loading process, which is
        triggered when we override the INSTALLED_APPS setting.
        """
        installed_apps = list(settings.INSTALLED_APPS)
        replaced_app_idx = installed_apps.index(
            "tests._site.apps.catalogue.apps.CatalogueConfig"
        )
        installed_apps[replaced_app_idx] = (
            "tests._site.import_error_app.catalogue.apps.CatalogueConfig"
        )
        with override_settings(INSTALLED_APPS=installed_apps):
            with self.assertRaises(ImportError):
                get_class("catalogue.import_error_module", "ImportErrorClass")


class ClassLoadingWithLocalOverrideTests(TestCase):
    def setUp(self):
        self.installed_apps = list(settings.INSTALLED_APPS)
        replaced_app_idx = self.installed_apps.index(
            "oscar.apps.shipping.apps.ShippingConfig"
        )
        self.installed_apps[replaced_app_idx] = (
            "tests._site.apps.shipping.apps.ShippingConfig"
        )

    def test_loading_class_defined_in_local_module(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Free,) = get_classes("shipping.methods", ("Free",))
            self.assertEqual("tests._site.apps.shipping.methods", Free.__module__)

    def test_loading_class_which_is_not_defined_in_local_module(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (FixedPrice,) = get_classes("shipping.methods", ("FixedPrice",))
            self.assertEqual("oscar.apps.shipping.methods", FixedPrice.__module__)

    def test_loading_class_from_module_not_defined_in_local_app(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Repository,) = get_classes("shipping.repository", ("Repository",))
            self.assertEqual("oscar.apps.shipping.repository", Repository.__module__)

    def test_loading_classes_defined_in_both_local_and_oscar_modules(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Free, FixedPrice) = get_classes("shipping.methods", ("Free", "FixedPrice"))
            self.assertEqual("tests._site.apps.shipping.methods", Free.__module__)
            self.assertEqual("oscar.apps.shipping.methods", FixedPrice.__module__)

    def test_loading_classes_with_root_app(self):
        import tests._site.shipping

        path = dirname(dirname(tests._site.shipping.__file__))
        with temporary_python_path([path]):
            replaced_app_idx = self.installed_apps.index(
                "tests._site.apps.shipping.apps.ShippingConfig"
            )
            self.installed_apps[replaced_app_idx] = "shipping.apps.ShippingConfig"
            with override_settings(INSTALLED_APPS=self.installed_apps):
                (Free,) = get_classes("shipping.methods", ("Free",))
                self.assertEqual("shipping.methods", Free.__module__)

    def test_overriding_view_is_possible_without_overriding_app(self):
        # If test fails, it's helpful to know if it's caused by order of
        # execution
        customer_app_config = CustomerConfig.create("oscar.apps.customer")
        customer_app_config.ready()
        self.assertEqual(
            customer_app_config.summary_view.__module__,
            "tests._site.apps.customer.views",
        )
        self.assertEqual(
            apps.get_app_config("customer").summary_view.__module__,
            "tests._site.apps.customer.views",
        )


class ClassLoadingWithLocalOverrideWithMultipleSegmentsTests(TestCase):
    def setUp(self):
        self.installed_apps = list(settings.INSTALLED_APPS)
        replaced_app_idx = self.installed_apps.index(
            "oscar.apps.shipping.apps.ShippingConfig"
        )
        self.installed_apps[replaced_app_idx] = (
            "tests._site.apps.shipping.apps.ShippingConfig"
        )

    def test_loading_class_defined_in_local_module(self):
        with override_settings(INSTALLED_APPS=self.installed_apps):
            (Free,) = get_classes("shipping.methods", ("Free",))
            self.assertEqual("tests._site.apps.shipping.methods", Free.__module__)


class TestOverridingCoreApps(TestCase):
    def test_means_the_overriding_model_is_registered_first(self):
        klass = get_model("partner", "StockRecord")
        self.assertEqual("tests._site.apps.partner.models", klass.__module__)


class TestAppLabelsForModels(TestCase):
    def test_all_oscar_models_have_app_labels(self):
        models = apps.get_models()
        missing = []
        for model in models:
            # Ignore non-Oscar models
            if "oscar" not in repr(model):
                continue
            # Don't know how to get the actual model's Meta class. But if
            # the parent doesn't have a Meta class, it's doesn't have an
            # base in Oscar anyway and is not intended to be overridden
            abstract_model = model.__base__
            meta_class = getattr(abstract_model, "Meta", None)
            if meta_class is None:
                continue

            if not hasattr(meta_class, "app_label"):
                missing.append(model)
        if missing:
            self.fail("Those models don't have an app_label set: %s" % missing)


class TestDynamicLoadingOn3rdPartyApps(TestCase):
    core_app_prefix = "thirdparty_package.apps"

    def setUp(self):
        self.installed_apps = list(settings.INSTALLED_APPS)
        sys.path.append("./tests/_site/")

    def tearDown(self):
        sys.path.remove("./tests/_site/")

    def test_load_core_3rd_party_class_correctly(self):
        self.installed_apps.append("thirdparty_package.apps.myapp.apps.MyAppConfig")
        with override_settings(INSTALLED_APPS=self.installed_apps):
            Cow, Goat = get_classes(
                "myapp.models", ("Cow", "Goat"), self.core_app_prefix
            )
            self.assertEqual("thirdparty_package.apps.myapp.models", Cow.__module__)
            self.assertEqual("thirdparty_package.apps.myapp.models", Goat.__module__)

    def test_load_overriden_3rd_party_class_correctly(self):
        self.installed_apps.append("tests._site.apps.myapp.apps.TestConfig")
        with override_settings(INSTALLED_APPS=self.installed_apps):
            Cow, Goat = get_classes(
                "myapp.models", ("Cow", "Goat"), self.core_app_prefix
            )
            self.assertEqual("thirdparty_package.apps.myapp.models", Cow.__module__)
            self.assertEqual("tests._site.apps.myapp.models", Goat.__module__)


class OverriddenClassLoadingTestCase(TestCase):
    def test_non_override_class_loader(self):
        from oscar.apps.catalogue.views import ProductDetailView

        View = get_class("catalogue.views", "ProductDetailView")
        self.assertEqual(View, ProductDetailView)

    @override_settings(
        OSCAR_DYNAMIC_CLASS_LOADER="tests._site.loader.custom_class_loader"
    )
    def test_override_class_loader(self):
        # Clear lru cache for the class loader
        get_class_loader.cache_clear()

        View = get_class("catalogue.views", "ProductDetailView")
        self.assertEqual(View, DummyClass)

        # Clear lru cache for the class loader again
        get_class_loader.cache_clear()
