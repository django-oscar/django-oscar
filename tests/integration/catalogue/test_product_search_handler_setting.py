from django.test import TestCase
from django.test.utils import override_settings

from oscar.apps.catalogue.search_handlers import get_product_search_handler_class, ProductSearchHandler


class TestSearchHandler(object):
    pass


class TestProductSearchHandlerSetting(TestCase):
    def test_get_product_search_handler_returns_OSCAR_PRODUCT_SEARCH_HANDLER_by_default(self):
        handler_override = 'tests.integration.catalogue.test_product_search_handler_setting.TestSearchHandler'
        with override_settings(OSCAR_PRODUCT_SEARCH_HANDLER=handler_override):
            self.assertEqual(get_product_search_handler_class(), TestSearchHandler)

    def test_get_product_search_handler_returns_OSCAR_PRODUCT_BROWSE_SEARCH_HANDLER_if_search_param_is_False(self):
        handler_override = 'tests.integration.catalogue.test_product_search_handler_setting.TestSearchHandler'
        with override_settings(OSCAR_PRODUCT_SEARCH_HANDLER='', OSCAR_PRODUCT_BROWSE_SEARCH_HANDLER=handler_override):
            self.assertEqual(get_product_search_handler_class(search=False), TestSearchHandler)

    def test_get_product_search_handler_returns_default_search_handler_class_if_no_setting_is_defined(self):
        """
            If search=True and OSCAR_PRODUCT_SEARCH_HANDLER is not defined,
            or search=False and OSCAR_PRODUCT_BROWSE_SEARCH_HANDLER is not defined,
            return catalogue.search_handlers.ProductSearchHandler
        """

        with override_settings(OSCAR_PRODUCT_SEARCH_HANDLER=None, OSCAR_PRODUCT_BROWSE_SEARCH_HANDLER=None):
            self.assertEqual(get_product_search_handler_class(search=True), ProductSearchHandler)
            self.assertEqual(get_product_search_handler_class(search=False), ProductSearchHandler)
