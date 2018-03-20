from django.conf import settings
from django.test import TestCase, override_settings

from elasticsearch_dsl import Q
from elasticsearch_dsl.faceted_search import FacetedResponse
from mock import patch, MagicMock
from oscar.test.factories import create_product

from oscar.apps.catalogue.documents import ProductDocument
from oscar.apps.catalogue.search import ProductSearch, PriceRangeSearch, RelatedProductSearch, TopProductsSearch


class ProductSearchTestCase(TestCase):

    def test_category_id_added_to_search_filters_if_supplied_and_filter_not_already_present(self):
        category_id = 18

        test_search = ProductSearch(category_id=category_id)

        self.assertEqual(test_search._search_filters['category'], {
            'type': 'term',
            'params': {'categories': category_id}
        })

    @patch.object(ProductSearch, 'build_search')
    def test_category_id_filter_not_added_if_other_category_filter_already_supplied(self, build_search_mock):
        category_id = 19

        test_search = ProductSearch(category_id=category_id, search_filters={'category': 'something-else'})

        self.assertEqual(test_search._search_filters['category'], 'something-else')

    def test_suggestion_applied_if_there_is_a_query(self):
        search = MagicMock()

        product_search = ProductSearch(query='Test Query')
        product_search.suggest(search)

        search.suggest.assert_called_with('suggestions', 'Test Query',
                                          phrase={'field': 'raw_title', 'size': 1, 'max_errors': 2.0})

    def test_build_search_calls_suggest(self):
        with patch.object(ProductSearch, 'suggest') as suggest_mock:
            ProductSearch(query='Test Query')

            suggest_mock.assert_called()

    def test_build_search_calls_filter_in_stock(self):
        with patch.object(ProductSearch, 'filter_in_stock') as filter_in_stock_mock:
            ProductSearch(query='Test Query')

            filter_in_stock_mock.assert_called()

    def test_filter_in_stock_not_applied_if_disabled_in_settings(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()

        search_mock = MagicMock()

        OSCAR_SEARCH['PRODUCTS']['filter_in_stock'] = False
        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            test_search = ProductSearch()
            test_search.filter_in_stock(search_mock)

            search_mock.filter.assert_not_called()

        OSCAR_SEARCH['PRODUCTS']['filter_in_stock'] = True
        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            test_search = ProductSearch()
            test_search.filter_in_stock(search_mock)
            search_mock.filter.assert_called()

    @override_settings(OSCAR_SEARCH={'PRODUCTS': {'filter_in_stock': True}})
    def test_filter_in_stock_filters_products_with_num_in_stock_bigger_than_zero(self):
        search_mock = MagicMock()

        test_search = ProductSearch()
        test_search.filter_in_stock(search_mock)

        search_mock.filter.assert_called_with('nested', path='stock', query=Q('range', stock__num_in_stock={'gt': 0}))

    @override_settings(OSCAR_SEARCH={'PRODUCTS': {'filter_in_stock': True}})
    def test_filter_in_stock_adds_currency_filter_if_present(self):
        search_mock = MagicMock()

        currency = 'KES'
        test_search = ProductSearch(currency=currency)
        test_search.filter_in_stock(search_mock)

        expected_query = Q('range', stock__num_in_stock={'gt': 0}) & Q('match', stock__currency=currency)

        search_mock.filter.assert_called_with('nested', path='stock', query=expected_query)


class PriceRangeSearchTestCase(TestCase):

    def test_aggregate_does_nothing(self):
        # would raise if it tried to do anything with the passed arg
        pr_search = PriceRangeSearch('KES')
        pr_search.aggregate(None)

    def test_sorts_by_price_ascending(self):
        search = MagicMock()
        sorted_search = MagicMock()
        search.sort.return_value = sorted_search

        pr_search = PriceRangeSearch('KES')
        pr_search.sort(search)

        search.sort.assert_called_with({
            'stock.price': {
                'order': 'asc',
                'mode': 'min',
                'nested_path': 'stock',
                'nested_filter': {
                    'match': {'stock.currency': 'KES'}
                }
            }
        })

    def test_extract_prices_returns_list_of_prices_from_results(self):
        pr_search = PriceRangeSearch(settings.OSCAR_DEFAULT_CURRENCY)

        p1 = create_product(price=200)
        p2 = create_product(price=300)

        results = FacetedResponse(pr_search.search(), {
            "hits": {
                "total": 150,
                "hits": [
                    {
                        '_source': {
                            'stock': ProductDocument().prepare_stock(p1)
                        }
                    },
                    {
                        '_source': {
                            'stock': ProductDocument().prepare_stock(p2)
                        }
                    }
                ]
            }
        })

        self.assertEqual(pr_search.extract_prices(results), [200, 300])

    def test_extract_prices_skips_products_with_different_currency(self):
        pr_search = PriceRangeSearch(settings.OSCAR_DEFAULT_CURRENCY)

        p1 = create_product(price=200)

        p2 = create_product(price=300)
        p2_sr = p2.stockrecords.first()
        p2_sr.price_currency = 'USD'
        p2_sr.save()

        results = FacetedResponse(pr_search.search(), {
            "hits": {
                "total": 150,
                "hits": [
                    {
                        '_source': {
                            'stock': ProductDocument().prepare_stock(p1)
                        }
                    },
                    {
                        '_source': {
                            'stock': ProductDocument().prepare_stock(p2)
                        }
                    }
                ]
            }
        })

        self.assertEqual(pr_search.extract_prices(results), [200])

    @patch.object(PriceRangeSearch, 'parse_price_ranges_results', return_value={'parsed': 'prices'})
    @patch.object(PriceRangeSearch, 'execute', return_value={'execute': 'results'})
    def test_get_price_ranges_executes_search_and_returns_parsed_prices_from_results(self, execute_mock,
                                                                                     parse_price_mock):
        test_search = PriceRangeSearch('KES')

        obj_list = test_search.get_price_ranges()

        execute_mock.assert_called()
        parse_price_mock.assert_called_with(execute_mock.return_value)

        self.assertEqual(obj_list, parse_price_mock.return_value)

    @patch.object(PriceRangeSearch, 'extract_prices', return_value=list(range(5)))
    def test_parse_price_ranges_results_does_nothing_if_number_of_prices_is_less_than_10(self,
                                                                                         extract_prices_mock):
        test_search = PriceRangeSearch('KES')
        self.assertIsNone(test_search.parse_price_ranges_results({}))

    @patch('oscar.apps.catalogue.search.utils.get_auto_ranges', return_value={'auto': 'ranges'})
    @patch('oscar.apps.catalogue.search.utils.chunks', return_value={'chunked': 'prices'})
    @patch.object(PriceRangeSearch, 'extract_prices', return_value=list(range(100)))
    def test_parse_price_range_results_calculates_price_group_size_based_on_number_of_prices_and_PRICE_FACET_COUNT_setting(self,
                                                                                                                           ep_mock,
                                                                                                                           chunks_mock,
                                                                                                                           get_auto_ranges_mock):
        # if we want 10 facets and there are 100 prices, there will be 10 prices per group
        expected_group_size = 10

        test_search = PriceRangeSearch('KES')

        with override_settings(OSCAR_SEARCH={'PRICE_FACET_COUNT': 10}):
            auto_ranges = test_search.parse_price_ranges_results({})

            chunks_mock.assert_called_with(list(range(100)), expected_group_size)
            get_auto_ranges_mock.assert_called_with(chunks_mock.return_value)

            self.assertEqual(auto_ranges, get_auto_ranges_mock.return_value)


class RelatedProductSearchTestCase(TestCase):

    def test_query_searches_more_like_this_with_given_product_ids(self):
        product_ids = [1, 2, 35]

        search_mock = MagicMock()

        with patch.object(RelatedProductSearch, 'search', return_value=search_mock):
            RelatedProductSearch(product_ids=product_ids)

            search_mock.query.assert_called_with('more_like_this',
                                                 fields=RelatedProductSearch.compare_fields,
                                                 ids=product_ids)

    def test_limit_count_applied_count(self):
        with patch.object(RelatedProductSearch, 'limit_count') as limit_count_mock:
            RelatedProductSearch([1], max_results=33)

            limit_count_mock.assert_called()

    @patch.object(RelatedProductSearch, 'obj_list_from_results', return_value={'obj': 'list'})
    @patch.object(RelatedProductSearch, 'execute', return_value={'execute': 'results'})
    def test_get_related_products_executes_search_and_returns_list_of_objects_from_results(self, execute_mock,
                                                                                           obj_list_mock):
        test_search = RelatedProductSearch([1])

        obj_list = test_search.get_related_products()

        execute_mock.assert_called()
        obj_list_mock.assert_called_with(execute_mock.return_value)

        self.assertEqual(obj_list, obj_list_mock.return_value)


class TopProductsSearchTestCase(TestCase):

    @patch.object(TopProductsSearch, 'obj_list_from_results', return_value={'obj': 'list'})
    @patch.object(TopProductsSearch, 'execute', return_value={'execute': 'results'})
    def test_get_top_products_executes_search_and_returns_list_of_objects_from_results(self, execute_mock,
                                                                                       obj_list_mock):
        test_search = TopProductsSearch()

        obj_list = test_search.get_top_products()

        execute_mock.assert_called()
        obj_list_mock.assert_called_with(execute_mock.return_value)

        self.assertEqual(obj_list, obj_list_mock.return_value)
