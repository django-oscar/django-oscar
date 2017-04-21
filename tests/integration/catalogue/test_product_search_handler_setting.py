from django.test import TestCase
from django.test.utils import override_settings

from oscar.apps.catalogue.search_handlers import (
    get_product_search_handler_class,
)


class TestSearchHandler(object):
    pass


class TestProductSearchHandlerSetting(TestCase):
    def test_product_search_handler_setting(self):
        """
        Test that the `OSCAR_PRODUCT_SEARCH_HANDLER` setting, when set,
        dictates the return value of the `get_product_search_handler_class`
        function.
        """
        handler_override = 'tests.integration.catalogue.test_product_search_handler_setting.TestSearchHandler'
        with override_settings(OSCAR_PRODUCT_SEARCH_HANDLER=handler_override):
            handler_class = get_product_search_handler_class()

        self.assertEqual(handler_class, TestSearchHandler)
