import mock

from django.conf import settings
from django.test import TestCase, override_settings
from oscar.test.factories import CategoryFactory
from oscar.test.utils import RequestFactory

from oscar.apps.catalogue.search_handlers import ProductSearchHandler


class ProductSearchHandlerFiltersTestCase(TestCase):

    @mock.patch.object(ProductSearchHandler, 'prepare_context')
    @mock.patch.object(ProductSearchHandler, 'get_results')
    def setUp(self, mock_get_results, mock_prepare_context):
        request = RequestFactory().post('/')
        self.search_handler = ProductSearchHandler(request.POST, '')

    def test_get_category_filters(self):
        self.assertIsNone(self.search_handler.get_category_filters({}))

        self.assertEqual({
            'type': 'term',
            'params': {'categories': 1}
        }, self.search_handler.get_category_filters({'category': '1'}))

        category = CategoryFactory()
        self.search_handler.categories = [category]
        self.assertEqual({
            'type': 'term',
            'params': {'categories': category.pk}
        }, self.search_handler.get_category_filters({}))

        last_category = CategoryFactory()
        self.search_handler.categories.append(last_category)

        self.assertEqual({
            'type': 'term',
            'params': {'categories': last_category.pk}
        }, self.search_handler.get_category_filters({}))

    def test_get_prices_filters_returns_none_if_price_min_isnt_set(self):
        self.assertIsNone(self.search_handler.get_price_filters({}))

    def test_get_prices_filters_sets_min_price(self):
        price_min = 100

        self.assertEqual({
            'type': 'nested',
            'params': {
                'path': 'stock',
                'query': {
                    'range': {
                        'stock.price': {
                            'gte': price_min
                        }
                    }
                }
            }
        }, self.search_handler.get_price_filters({'price_min': price_min}))

    def test_get_prices_filters_sets_max_price_if_available(self):
        price_min = 100
        price_max = 125

        self.assertEqual({
            'type': 'nested',
            'params': {
                'path': 'stock',
                'query': {
                    'range': {
                        'stock.price': {
                            'gte': price_min,
                            'lte': price_max
                        }
                    }
                }
            }
        }, self.search_handler.get_price_filters({'price_min': price_min, 'price_max': price_max}))

    def test_get_num_in_stock_filters(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['HIDE_OOS_FROM_CATEGORY_VIEW'] = False

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            self.assertEqual(None, self.search_handler.get_num_in_stock_filters({}))

        OSCAR_SEARCH['HIDE_OOS_FROM_CATEGORY_VIEW'] = True
        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            self.assertEqual({
                'type': 'nested',
                'params': {
                    'path': 'stock',
                    'query': {
                        'range': {
                            'stock.num_in_stock': {'gt': 0}
                        }
                    }
                }
            }, self.search_handler.get_num_in_stock_filters({}))

    def test_get_currency_filters(self):
        currency = 'CUR'
        self.search_handler.currency = currency

        self.assertEqual({
            'type': 'nested',
            'params': {
                'path': 'stock',
                'query': {
                    'match': {'stock.currency': currency}
                }
            }
        }, self.search_handler.get_currency_filters({}))

    def test_get_filters_returns_filters_defined_in_applied_filters(self):
        filter_form_data = {'category': 1, 'price_min': 100}

        applied_filters = ['currency', 'category']
        self.search_handler.applied_filters = applied_filters

        self.assertEqual(sorted(self.search_handler.get_filters(filter_form_data).keys()), sorted(applied_filters))

        applied_filters.append('price')
        self.assertEqual(sorted(self.search_handler.get_filters(filter_form_data).keys()), sorted(applied_filters))
