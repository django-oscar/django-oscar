from copy import deepcopy

from elasticsearch_dsl.faceted_search import FacetedResponse
from mock import patch, MagicMock

from django.conf import settings
from django.test import TestCase, override_settings
from elasticsearch_dsl import TermsFacet, RangeFacet, Q, AttrDict
from oscar.test.factories import create_product

from oscar.apps.search.utils import ESPaginator
from tests._site.search_tests_app.models import SearchModel

from tests._site.search_tests_app.search import Search, AutoSuggestSearch


class SearchTestCase(TestCase):

    def test_doc_type_returns_document_type_name(self):
        self.assertEqual(Search().doc_type, 'test')

    def test_aggregation_skipped_if_search_setting_AGGREGATE_SEARCH_is_false(self):
        OSCAR_SEARCH = deepcopy(settings.OSCAR_SEARCH)
        OSCAR_SEARCH['TEST_SEARCH']['facets'] = {
            'manufacturer': {
                'type': 'terms',
                'label': 'Manufacturer',
                'params': {'field': 'manufacturer.keyword'}
            }
        }

        search_mock = MagicMock()

        OSCAR_SEARCH['TEST_SEARCH']['aggregate_search'] = False
        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            test_search = Search()
            test_search.aggregate(search_mock)

            search_mock.aggs.bucket.assert_not_called()

        OSCAR_SEARCH['TEST_SEARCH']['aggregate_search'] = True
        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            test_search = Search()
            test_search.aggregate(search_mock)

            search_mock.aggs.bucket.assert_called()

    def test_get_main_facets_returns_user_defined_facets(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['TEST_SEARCH']['facets'] = {
            'manufacturer': {
                'type': 'terms',
                'label': 'Manufacturer',
                'params': {'field': 'manufacturer.keyword'}
            },
            'size': {
                'type': 'range',
                'label': 'Size',
                'params': {
                    'field': 'size',
                    'ranges': [
                        ("Below 21", (None, 21)),
                        ("21 to 24", (21, 24)),
                        ("24 to 31", (24, 31)),
                        ("Above 31", (31, None))
                    ]
                }
            },
        }

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            test_search = Search()

            main_facets = test_search.get_main_facets()
            self.assertEqual(sorted(main_facets.keys()), sorted(['manufacturer', 'size']))

            manufacturer_facet = main_facets['manufacturer']
            size_facet = main_facets['size']

            self.assertIsInstance(manufacturer_facet, TermsFacet)
            self.assertIsInstance(size_facet, RangeFacet)

            self.assertEqual(manufacturer_facet._params, {'field': 'manufacturer.keyword'})
            self.assertEqual(size_facet._params, {
                'field': 'size',
                'keyed': False,
                'ranges': [
                    {'to': 21, 'key': 'Below 21'},
                    {'from': 21, 'to': 24, 'key': '21 to 24'},
                    {'from': 24, 'to': 31, 'key': '24 to 31'},
                    {'from': 31, 'key': 'Above 31'}
                ]
            })

    def test_get_main_facets_handles_adds_size_param_for_auto_ranges_and_adds_them_to_auto_ranges_list(self):
        OSCAR_SEARCH = deepcopy(settings.OSCAR_SEARCH)
        OSCAR_SEARCH['TEST_SEARCH']['facets'] = {
            'manufacturer': {
                'type': 'terms',
                'label': 'Manufacturer',
                'params': {'field': 'manufacturer.keyword'}
            },
            'size': {
                'type': 'auto_range',
                'label': 'Size',
                'group_count': 1,
                'params': {'field': 'size'}
            }
        }

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            test_search = Search()
            main_facets = test_search.get_main_facets()

            self.assertEqual(main_facets['size']._params, {
                'field': 'size',
                'size': 1000000
            })

            self.assertEqual(test_search.auto_ranges, {
                'size': {
                    'type': 'auto_range',
                    'label': 'Size',
                    'group_count': 1,
                    'params': {'field': 'size', 'size': 1000000}
                }
            })

    def test_facets_contains_main_facets_and_extra_facets(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['TEST_SEARCH'] = {
            'facets': {
                'manufacturer': {
                    'type': 'terms',
                    'label': 'Manufacturer',
                    'params': {'field': 'manufacturer.keyword'}
                }
            },
            'aggregate_search': True
        }

        extra_facets = {
            'category': TermsFacet(field='categories')
        }

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            with patch.object(Search, 'get_extra_facets', return_value=extra_facets):
                test_search = Search()

                self.assertEqual(sorted(test_search.facets.keys()), sorted(['manufacturer', 'category']))

    def test_search_method_returns_documents_search_instance(self):
        test_search = Search()

        search_instance = test_search.search()

        self.assertEqual(search_instance._doc_type, [test_search.document._doc_type.name])
        self.assertEqual(search_instance._model, test_search.document._doc_type.model)

    def test_query_returns_query_config_defined_in_settings(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['TEST_SEARCH']['query'] = {
            "query_type": "multi_match",
            "fields": ["all_skus", "upc", "title^2", "description"]
        }

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            search = MagicMock()

            test_search = Search()
            test_search.query(search, 'q')

            search.query.assert_called_with(
                'multi_match',
                query='q',
                fields=["all_skus", "upc", "title^2", "description"]
            )

    def test_search_filters(self):
        search_filters = {
            'currency': {
                'type': 'nested',
                'params': {
                    'path': 'stock',
                    'query': {
                        'match': {'stock.currency': 'KES'}
                    }
                }
            }
        }

        test_search = Search(search_filters=search_filters)

        search = MagicMock()

        test_search.search_filters(search)

        search.filter.assert_called_with(
            Q('nested', path='stock', query={'match': {'stock.currency': 'KES'}})
        )

    def test_build_search_applies_search_filters(self):
        with patch.object(Search, 'search_filters') as mock_search_filter:
            Search()
            mock_search_filter.assert_called()

    def test_limit_source_fields(self):
        search_mock = MagicMock()

        test_search = Search()
        test_search.source_fields = ['field1', 'field2']

        test_search.limit_source(search_mock)

        search_mock.source.assert_called_with(['field1', 'field2'])

    def test_limit_source_fields_called_in_build_search(self):
        with patch.object(Search, 'limit_source') as limit_source_mock:
            Search()
            limit_source_mock.assert_called()

    def test_limit_count(self):
        search_mock = MagicMock()

        test_search = Search(max_results=12)
        test_search.limit_count(search_mock)

        search_mock.__getitem__.assert_called_with(slice(0, 12))

    def test_limit_count_calculates_start_offset_and_end_offset_according_to_supplied_page_number(self):
        search_mock = MagicMock()

        test_search = Search(page_number=3, max_results=12)
        test_search.limit_count(search_mock)

        search_mock.__getitem__.assert_called_with(slice(24, 36))

    def test_limit_count_called_in_build_search(self):
        with patch.object(Search, 'limit_count') as limit_count_mock:
            Search()
            limit_count_mock.assert_called()

    def test_obj_list_from_results_loads_objects_from_database(self):
        product1 = SearchModel.objects.create(title='test1')
        product2 = SearchModel.objects.create(title='test2')

        p1_dict = AttrDict({
            'meta': {
                'id': product1.id
            }
        })
        p2_dict = AttrDict({
            'meta': {
                'id': product2.id
            }
        })

        results = [
            p1_dict,
            p2_dict
        ]

        test_search = Search()
        objects = test_search.obj_list_from_results(results)

        self.assertEqual(objects, [product1, product2])

    def test_obj_list_from_results_maintains_order_of_objects_in_results(self):
        p1 = SearchModel.objects.create(title='test1')
        p2 = SearchModel.objects.create(title='test2')
        p3 = SearchModel.objects.create(title='test3')

        p1_dict = AttrDict({
            'meta': {
                'id': p1.id
            }
        })
        p2_dict = AttrDict({
            'meta': {
                'id': p2.id
            }
        })
        p3_dict = AttrDict({
            'meta': {
                'id': p3.id
            }
        })

        test_search = Search()

        self.assertEqual(
            test_search.obj_list_from_results([p2_dict, p1_dict, p3_dict]),
            [p2, p1, p3]
        )

        self.assertNotEqual(
            test_search.obj_list_from_results([p2_dict, p1_dict, p3_dict]),
            [p2, p3, p1]
        )

        self.assertEqual(
            test_search.obj_list_from_results([p1_dict, p3_dict, p2_dict]),
            [p1, p3, p2]
        )

    def test_aggregation_extraction(self):
        results = AttrDict({
            'aggregations': {
                "_filter_size": {
                    "doc_count": 150,
                    "size": {
                        "doc_count_error_upper_bound": 0,
                        "sum_other_doc_count": 0,
                        "buckets": [
                            {
                                "key": "10'",
                                "doc_count": 5
                            },
                            {
                                "key": "12'",
                                "doc_count": 5
                            },
                            {
                                "key": "13'",
                                "doc_count": 8
                            }
                        ]
                    }
                },
                "_filter_color": {
                    "doc_count": 150,
                    "color": {
                        "doc_count_error_upper_bound": 0,
                        "sum_other_doc_count": 0,
                        "buckets": [
                            {
                                "key": "Red",
                                "doc_count": 2
                            },
                            {
                                "key": "Purple",
                                "doc_count": 18
                            }
                        ]
                    }
                },
                "_filter_excluded_aggregation": {
                    "doc_count": 150,
                    "excluded_aggregation": {
                        "doc_count_error_upper_bound": 0,
                        "sum_other_doc_count": 0,
                        "buckets": [
                            {
                                "key": "Bad attribute",
                                "doc_count": 12
                            },
                            {
                                "key": "Badder attribute",
                                "doc_count": 10
                            }
                        ]
                    }
                }
            }
        })

        expected_facets = {
            'doc_count': 150,
            'size': {
                "doc_count_error_upper_bound": 0,
                "sum_other_doc_count": 0,
                "buckets": [
                    {
                        "key": "10'",
                        "doc_count": 5
                    },
                    {
                        "key": "12'",
                        "doc_count": 5
                    },
                    {
                        "key": "13'",
                        "doc_count": 8
                    }
                ]
            },
            'color': {
                "doc_count_error_upper_bound": 0,
                "sum_other_doc_count": 0,
                "buckets": [
                    {
                        "key": "Red",
                        "doc_count": 2
                    },
                    {
                        "key": "Purple",
                        "doc_count": 18
                    }
                ]
            }
        }

        test_search = Search()
        self.assertEqual(
            test_search.extract_facets(results, ['size', 'color']),
            expected_facets
        )

    def test_suggestion_extraction(self):
        expected_suggestion = 'samsung'

        results = AttrDict({
            "suggest": {
                'suggestions': [
                    {
                        'options': [{'text': expected_suggestion, 'score': 0.19034192}],
                        'offset': 0,
                        'text': 'somsung',
                        'length': 7
                    }
                ]
            }
        })

        self.assertEqual(Search().extract_suggestion(results), expected_suggestion)

    def test_paginate_objects(self):
        objects = [create_product(), create_product()]

        test_search = Search(max_results=1)

        paginator = test_search.paginate_objects(objects, 2)

        self.assertIsInstance(paginator, ESPaginator)
        self.assertEqual(paginator.num_pages, 2)

    def test_parse_results(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['TEST_SEARCH']['facets'] = {
            'manufacturer': {
                'type': 'terms',
                'label': 'Manufacturer',
                'params': {'field': 'manufacturer.keyword'}
            }
        }

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            p1 = create_product()

            extra_facets = {
                'category': TermsFacet(field='categories')
            }

            with patch.object(Search, 'get_extra_facets', return_value=extra_facets):
                test_search = Search()

                results = FacetedResponse(test_search.search(), {
                    "hits": {
                        "total": 150,
                        "hits": [
                            {
                                '_type': 'product',
                                '_index': 'regulus',
                                '_id': p1.id,
                                '_source': {'title': p1.title}
                            }
                        ]
                    },
                    "suggest": {
                        'suggestions': [
                            {
                                'options': [{'text': 'samsung', 'score': 0.19034192}],
                                'offset': 0,
                                'text': 'somsung',
                                'length': 7
                            }
                        ]
                    },
                    "aggregations": {
                        "_filter_manufacturer": {
                            "doc_count": 150,
                            "manufacturer": {
                                "doc_count_error_upper_bound": 0,
                                "sum_other_doc_count": 0,
                                "buckets": [
                                    {
                                        "key": "Samsung",
                                        "doc_count": 150
                                    }
                                ]
                            }
                        },
                        "_filter_category": {
                            "doc_count": 150,
                            "category": {
                                'sum_other_doc_count': 0,
                                'doc_count_error_upper_bound': 0,
                                'buckets': [
                                    {'key': 16, 'doc_count': 70},
                                    {'key': 17, 'doc_count': 70},
                                    {'key': 18, 'doc_count': 43}
                                ]
                            }
                        }
                    }
                })

                parsed_results = test_search.parse_results(results)

                objects = test_search.obj_list_from_results(results)

                expected_parsed_results = {
                    'total': 150,
                    'objects': test_search.obj_list_from_results(results),
                    'facets': test_search.extract_facets(results, ['manufacturer']),
                    'other_aggs': test_search.extract_facets(results, ['category']),
                    'paginator': test_search.paginate_objects(objects, 150),
                    'suggestion': test_search.extract_suggestion(results)
                }

                for key in parsed_results.keys():
                    if key == 'paginator':
                        continue

                    self.assertEqual(parsed_results[key], expected_parsed_results[key])

                self.assertEqual(
                    parsed_results['paginator'].object_list.object_list,
                    expected_parsed_results['paginator'].object_list.object_list
                )
                self.assertEqual(
                    parsed_results['paginator'].object_list.total,
                    expected_parsed_results['paginator'].object_list.total
                )
                self.assertEqual(
                    parsed_results['paginator'].per_page,
                    expected_parsed_results['paginator'].per_page
                )

    @patch.object(Search, 'parse_results', return_value={'parse': 'results'})
    @patch.object(Search, 'execute', return_value={'exec': 'ute'})
    def test_get_search_results(self, mock_execute, mock_parse_results):
        test_search = Search()
        search_results = test_search.get_search_results()

        self.assertEqual(search_results, mock_parse_results.return_value)

        mock_execute.assert_called_once()
        mock_parse_results.assert_called_with(mock_execute.return_value)

    def test_get_auto_range_group_size(self):
        test_search = Search()

        # if we expect 5 groups and the number of values is 100, then group size will be 20
        test_search.auto_ranges['size'] = {
            'group_count': 5
        }

        self.assertEqual(test_search.get_auto_range_group_size('size', list(range(100))), 20)

    def test_get_auto_range_group_size_if_fewer_values_than_groups(self):
        test_search = Search()

        test_search.auto_ranges['size'] = {
            'group_count': 5
        }
        # We only have 2 unique values, so should return a size of 2, and ignore group_count
        values = [0, 1, 1, 1]

        self.assertEqual(test_search.get_auto_range_group_size('size', values), 2)

    def test_get_auto_range_group_size_if_too_few_unique_values(self):
        test_search = Search()

        test_search.auto_ranges['size'] = {
            'group_count': 5
        }
        # Only one unique value - we cannot make a meaningful range facet
        values = [1, 1, 1, 1]

        self.assertEqual(test_search.get_auto_range_group_size('size', values), None)

    def test_auto_range_to_range_facet_returns_empty_dict_if_no_buckets_were_received(self):
        self.assertEqual(Search().auto_range_to_range_facet('', {'buckets': []}), {})


class AutoSuggestSearchTestCase(TestCase):

    def test_highlight_method_just_returns_the_search_instance_without_doing_anything(self):
        search_instance = None

        test_search = AutoSuggestSearch(query='q')

        self.assertEqual(test_search.highlight(search_instance), search_instance)

    def test_parse_suggestions(self):
        test_search = AutoSuggestSearch(query='q')

        p1 = SearchModel.objects.create(title='Test1')
        p2 = SearchModel.objects.create(title='Test2')

        results = FacetedResponse(test_search.search(), {
            "hits": {
                "total": 2,
                "hits": [
                    {
                        '_type': 'product',
                        '_index': 'regulus',
                        '_id': p1.id,
                        '_source': {'title': p1.title}
                    },
                    {
                        '_type': 'product',
                        '_index': 'regulus',
                        '_id': p2.id,
                        '_source': {'title': p2.title}
                    }
                ]
            }
        })

        expected_parsed_results = {
            'count': 2,
            'results': [
                {
                    'title': p1.title
                },
                {
                    'title': p2.title
                }
            ]
        }

        self.assertEqual(test_search.parse_suggestions(results), expected_parsed_results)

    @patch.object(AutoSuggestSearch, 'parse_suggestions', return_value={'parse': 'suggestions'})
    @patch.object(AutoSuggestSearch, 'execute', return_value={'exec': 'ute'})
    def test_get_suggestions_executes_search_and_returns_parsed_results(self, execute_mock, parse_suggestions_mock):
        test_search = AutoSuggestSearch(query='q')
        suggestions = test_search.get_suggestions()

        self.assertEqual(suggestions, parse_suggestions_mock.return_value)

        execute_mock.assert_called_once()
        parse_suggestions_mock.assert_called_with(execute_mock.return_value)
