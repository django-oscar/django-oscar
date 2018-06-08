from collections import OrderedDict

from elasticsearch_dsl.faceted_search import FacetedResponse
from elasticsearch_dsl.query import Term
from unittest.mock import patch, MagicMock

from django.test import TestCase
from elasticsearch_dsl import TermsFacet, Q, AttrDict
from oscar.apps.es_search.faceted_search import AutoRangeFacet
from oscar.test.factories import create_product

from oscar.apps.es_search.utils import ESPaginator, get_auto_ranges
from tests._site.search_tests_app.models import SearchModel

from tests._site.search_tests_app.search import Search, AutoSuggestSearch


class SearchTestCase(TestCase):

    def test_doc_type_returns_document_type_name(self):
        self.assertEqual(Search().doc_type, 'test_search_doc')

    def test_aggregation_skipped_if_search_setting_AGGREGATE_SEARCH_is_false(self):
        search_mock = MagicMock()

        test_search = Search()
        test_search.facets = {
            'manufacturer': TermsFacet(field='manufacturer.keyword')
        }
        test_search.aggregate_search = False
        test_search.aggregate(search_mock)

        search_mock.aggs.bucket.assert_not_called()

        test_search.aggregate_search = True
        test_search.aggregate(search_mock)

        self.assertTrue(search_mock.aggs.bucket.called)

    def test_search_method_returns_documents_search_instance(self):
        test_search = Search()

        search_instance = test_search.search()

        self.assertEqual(search_instance._doc_type, [test_search.document])
        self.assertEqual(search_instance._model, test_search.document._doc_type.model)

    def test_query_returns_query_config_defined_in_settings(self):
        search = MagicMock()

        test_search = Search()
        test_search.query(search, 'q')

        expected_call_arg = test_search.query_config.copy()
        expected_call_arg['query'] = 'q'
        search.query.assert_called_with(
            expected_call_arg.pop('query_type'),
            **expected_call_arg
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
            self.assertTrue(mock_search_filter.called)

    def test_limit_source_fields(self):
        search_mock = MagicMock()

        test_search = Search()
        test_search.source_fields = ['field1', 'field2']

        test_search.limit_source(search_mock)

        search_mock.source.assert_called_with(['field1', 'field2'])

    def test_limit_source_fields_called_in_build_search(self):
        with patch.object(Search, 'limit_source') as limit_source_mock:
            Search()
            self.assertTrue(limit_source_mock.called)

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
            self.assertTrue(limit_count_mock.called)

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
        test_search.facets = {
            'size': {},
            'color': {}
        }
        self.assertEqual(
            test_search.extract_facets(results),
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
        p1 = create_product()

        test_search = Search()
        test_search.facets = {
            'manufacturer': TermsFacet(field='manufacturer.keyword'),
            'category': TermsFacet(field='categories')
        }

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
            'facets': test_search.extract_facets(results),
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

        self.assertEqual(mock_execute.call_count, 1)
        mock_parse_results.assert_called_with(mock_execute.return_value)

    def test_get_auto_range_group_size(self):
        test_search = Search()

        # if we expect 5 groups and the number of values is 100, then group size will be 20
        test_search.facets = {
            'size': AutoRangeFacet(group_count=5, field='size')
        }

        self.assertEqual(test_search.get_auto_range_group_size('size', list(range(100))), 20)

    def test_get_auto_range_group_size_if_fewer_values_than_groups(self):
        test_search = Search()

        test_search.facets = {
            'size': AutoRangeFacet(group_count=5, field='size')
        }
        # We only have 2 unique values, so should return a size of 2, and ignore group_count
        values = [0, 1, 1, 1]

        self.assertEqual(test_search.get_auto_range_group_size('size', values), 2)

    def test_get_auto_range_group_size_if_too_few_unique_values(self):
        test_search = Search()

        test_search.facets = {
            'size': AutoRangeFacet(group_count=5, field='size')
        }
        # Only one unique value - we cannot make a meaningful range facet
        values = [1, 1, 1, 1]

        self.assertEqual(test_search.get_auto_range_group_size('size', values), None)

    def test_auto_range_to_range_facet_returns_empty_dict_if_no_buckets_were_received(self):
        self.assertEqual(Search().auto_range_to_range_facet('', {'buckets': []}), {})

    def test_add_selected_facets_filters(self):
        test_search = Search()
        test_search.facets = {
            'title': TermsFacet(field='title')
        }
        test_search.aggregate_search = True

        selected_facets = {
            'title': ['First title']
        }
        self.assertEqual(
            test_search.add_selected_facets_filters(selected_facets),
            [Term(title='First title')]
        )

        self.assertEqual(
            test_search._facet_filters['title'],
            Term(title='First title')
        )

    def test_selected_facets_added_to_selected_facets_filters_in_init(self):
        selected_facets = {
            'title': ['First title']
        }
        test_search = Search(selected_facets=selected_facets)
        self.assertEqual(
            test_search.selected_facets_filters,
            test_search.add_selected_facets_filters(selected_facets)
        )

    def test_filter_selected_facets(self):
        selected_facets = {
            'title': ['First title'],
            'description': ['Model description']
        }
        selected_facets = OrderedDict(sorted(selected_facets.items(), key=lambda t: t[0]))

        class TestSearch(Search):
            facets = {
                'title': TermsFacet(field='title'),
                'description': TermsFacet(field='description')
            }

        test_search = TestSearch(selected_facets=selected_facets)
        test_search.aggregate_search = True
        search = MagicMock()
        test_search.filter_selected_facets(search)

        search.post_filter.assert_called_with(
            Q('match_all') & Term(description='Model description') & Term(title='First title')
        )

    def test_auto_range_to_range_facet_return_value(self):
        facet_data = {
            'buckets': [
                {'key': 1, 'doc_count': 5},
                {'key': 5, 'doc_count': 5},
                {'key': 10, 'doc_count': 5},
                {'key': 20, 'doc_count': 10}
            ]
        }
        facet_name = 'size'

        test_search = Search()
        test_search.facets = {
            'size': AutoRangeFacet(group_count=2, field='size')
        }
        test_search.aggregate_search = True

        chunks = (
            [1, 1], [1, 1], [1, 5], [5, 5], [5, 5], [10, 10],
            [10, 10], [10, 20], [20, 20], [20, 20], [20, 20],
            [20, 20, 20]
        )

        self.assertEqual(
            test_search.auto_range_to_range_facet(facet_name, facet_data),
            {
                facet_name: {
                    'buckets': get_auto_ranges(chunks)
                }
            }
        )

    def test_auto_range_to_range_facet_returns_empty_dict_if_group_size_is_None(self):
        facet_data = {
            'buckets': [
                {'key': 1, 'doc_count': 1},
            ]
        }
        facet_name = 'size'

        test_search = Search()
        test_search.aggregate_search = True
        test_search.facets = {
            'size': AutoRangeFacet(group_count=2, field='size')
        }
        self.assertEqual(
            test_search.auto_range_to_range_facet(facet_name, facet_data),
            {}
        )

    def test_extract_facets_adds_processed_auto_ranges_to_return_value(self):
        facet_name = 'size'
        results = AttrDict({
            'aggregations': {
                '_filter_size': {
                    'size': {
                        'buckets': [
                            {'key': 1, 'doc_count': 5},
                            {'key': 5, 'doc_count': 5}
                        ]
                    }
                }
            }
        })

        test_search = Search()
        test_search.aggregate_search = True
        test_search.facets = {
            'size': AutoRangeFacet(group_count=2, field='size')
        }
        extracted_facets = test_search.extract_facets(results)

        self.assertEqual(
            extracted_facets,
            test_search.auto_range_to_range_facet(facet_name, results['aggregations']['_filter_size']['size'])
        )

    def test_parse_results_adds_facets_if_aggregate_search_is_True(self):
        results = AttrDict({
            'hits': {
                'total': 100,
            },
            'aggregations': {
                '_filter_title': {
                    'title': {
                        'buckets': [
                            {'key': 'First title'},
                        ]
                    }
                }
            }
        })

        test_search = Search()
        test_search.aggregate_search = True
        test_search.facets = {
            'title': TermsFacet(field='title')
        }
        test_search.obj_list_from_results = MagicMock(return_value=[])

        parsed_results = test_search.parse_results(results)

        self.assertEqual(
            parsed_results['facets'],
            test_search.extract_facets(results)
        )


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

        self.assertEqual(execute_mock.call_count, 1)
        parse_suggestions_mock.assert_called_with(execute_mock.return_value)
