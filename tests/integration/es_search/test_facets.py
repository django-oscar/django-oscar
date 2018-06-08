from collections import OrderedDict

from django.test import TestCase
from elasticsearch_dsl import faceted_search, TermsFacet
from oscar.apps.es_search.faceted_search import AutoRangeFacet
from purl import URL
from oscar.apps.es_search.facet import Facet, FacetsBuilder, HistogramFacet, RangeFacet

from tests._site.search_tests_app.search import Search


class FacetTestCase(TestCase):

    def setUp(self):
        self.search_class = Search()

    def test_get_field_value_returns_bucket_key(self):
        facet = Facet('agg_name', {'buckets': []}, 'http://example.com', {})

        self.assertEqual(
            'Yes',
            facet.get_field_value({'key': 'Yes', 'doc_count': 90})
        )

    def test_get_display_name_returns_get_field_value_value(self):
        facet = Facet('agg_name', {'buckets': []}, 'http://example.com', {})

        bucket = {'key': 'Yes', 'doc_count': 90}
        self.assertEqual(
            facet.get_display_name(bucket),
            facet.get_field_value(bucket)
        )

    def test_get_select_url_adds_selected_facets_param(self):
        facet_name = 'agg_name'
        facet_value = 'agg_value'

        facet = Facet(facet_name, {'buckets': []}, 'http://example.com/', {})
        self.assertEqual(
            facet.get_select_url(facet_value),
            'http://example.com/?selected_facets={}%3A{}'.format(facet_name, facet_value)
        )

        facet = Facet(facet_name, {'buckets': []}, 'http://example.com/?selected_facets=diff_agg:diff_value', {})
        self.assertEqual(
            facet.get_select_url(facet_value),
            'http://example.com/?selected_facets=diff_agg%3Adiff_value&selected_facets={}%3A{}'.format(facet_name, facet_value)
        )

    def test_get_deselect_url_removes_selected_facets_param(self):
        facet_name = 'agg_name'
        facet_value = 'agg_value'

        facet = Facet(facet_name, {'buckets': []}, 'http://example.com/?selected_facets={}%3A{}'.format(facet_name, facet_value), {})
        self.assertEqual(
            facet.get_deselect_url(facet_value),
            'http://example.com/'
        )

        facet = Facet(facet_name, {'buckets': []},
                      'http://example.com/?selected_facets=diff_agg%3Adiff_value&selected_facets={}%3A{}'.format(facet_name, facet_value),
                      {})
        self.assertEqual(
            facet.get_deselect_url(facet_value),
            'http://example.com/?selected_facets=diff_agg%3Adiff_value'
        )

    def test_build_facet_return_value(self):
        facet = Facet('agg_name', {}, 'http://example.com', search_class=self.search_class)
        self.assertEqual(
            {
                'name': 'Yes',
                'count': 12,
                'show_count': True,
                'selected': False,
                'disabled': False,
                'select_url': 'http://example.com?selected_facets=agg_name%3AYes'
            },
            facet.build_facet_result({
                'key': 'Yes',
                'doc_count': 12
            })
        )

        self.assertEqual(
            {
                'name': 'No',
                'count': 10,
                'show_count': True,
                'selected': False,
                'disabled': False,
                'select_url': 'http://example.com?selected_facets=agg_name%3ANo'
            },
            facet.build_facet_result({
                'key': 'No',
                'doc_count': 10
            })
        )

    def test_build_facet_adds_deselect_url_and_sets_selected_to_True_if_facet_is_selected(self):
        facet = Facet('agg_name', {}, 'http://example.com?selected_facets=agg_name%3ANo', {}, {'agg_name': ['No']})
        self.assertEqual(
            {
                'name': 'No',
                'count': 10,
                'show_count': True,
                'disabled': False,
                'deselect_url': 'http://example.com',
                'selected': True,
            },
            facet.build_facet_result({
                'key': 'No',
                'doc_count': 10
            })
        )

    def test_strip_pagination_removes_page_param(self):
        self.assertEqual(
            'http://oscar.com/',
            Facet.strip_pagination(URL('http://oscar.com/?page=10'))
        )
        self.assertEqual(
            'http://oscar.com/?query=q',
            Facet.strip_pagination(URL('http://oscar.com/?page=10&query=q'))
        )

    def test_get_display_name_uses_label_defined_in_search_class_facet_display_dict(self):
        self.search_class.facet_display = OrderedDict([
            ('agg_name', 'Agg name')
        ])

        facet = Facet('agg_name', {}, 'http://example.com', search_class=self.search_class)

        self.assertEqual(
            facet.get_facet_display_name(),
            'Agg name'
        )

    def test_get_display_name_falls_back_to_capitalized_field_name_if_label_not_supplied(self):
        facet = Facet('agg_name', {}, 'http://example.com', search_class=self.search_class)

        self.assertEqual(
            facet.get_facet_display_name(),
            'Agg_name'
        )

    def test_get_facet_results(self):
        facet = Facet('agg_name',
                      {'buckets': [{'key': 'Yes', 'doc_count': 12}, {'key': 'No', 'doc_count': 0}]},
                      'http://example.com', search_class=self.search_class)

        self.assertEqual(
            {
                'results': [{
                    'name': 'Yes',
                    'count': 12,
                    'show_count': True,
                    'selected': False,
                    'disabled': False,
                    'select_url': 'http://example.com?selected_facets=agg_name%3AYes'
                }, {
                    'name': 'No',
                    'count': 0,
                    'show_count': True,
                    'selected': False,
                    'disabled': True,
                    'select_url': 'http://example.com?selected_facets=agg_name%3ANo'}
                ],
                'name': 'Agg_name'
            },
            facet.get_facet()
        )


class RangeFacetTestCase(TestCase):

    def setUp(self):
        self.search_class = Search()

    def test_get_field_value_formatting(self):
        self.assertEqual(
            '10-40',
            RangeFacet.get_field_value({
                'from': '10',
                'to': '40'
            })
        )

    def test_get_display_name_return_value_with_both_to_and_from_values(self):
        bucket = {
            'from': 10,
            'to': 40
        }

        self.assertEqual(
            '10 to 40',
            RangeFacet.get_display_name(bucket)
        )

    def test_get_display_name_return_value_with_only_to_value(self):
        bucket = {
            'to': 40
        }

        self.assertEqual(
            'Up to 40',
            RangeFacet.get_display_name(bucket)
        )

    def test_get_display_name_return_value_with_only_from_value(self):
        bucket = {
            'from': 10
        }

        self.assertEqual(
            '10 and above',
            RangeFacet.get_display_name(bucket)
        )

    def test_empty_list_returned_if_all_buckets_have_doc_count_of_zero(self):
        buckets = [
            {
                'doc_count': 0
            },
            {
                'doc_count': 0
            }
        ]
        facet = RangeFacet('agg_name', {'buckets': buckets}, 'http://example.com', search_class=self.search_class)

        self.assertEqual(
            {'results': [], 'name': 'Agg_name'},
            facet.get_facet()
        )

    def test_get_facet_returns_normal_facet_if_total_doc_count_more_than_zero(self):
        buckets = [
            {
                "key": "Up to 40",
                "to": 40,
                "doc_count": 0
            },
            {
                "key": "41 to 60",
                "from": 41,
                "to": 60,
                "doc_count": 10
            }
        ]

        expected_results = [
            {
                'name': 'Up to 40',
                'count': 0,
                'show_count': True,
                'selected': False,
                'disabled': True,
                'select_url': 'http://example.com?selected_facets=agg_name%3A-40'
            },
            {
                'name': '41 to 60',
                'count': 10,
                'show_count': True,
                'selected': False,
                'disabled': False,
                'select_url': 'http://example.com?selected_facets=agg_name%3A41-60'
            }
        ]

        facet = RangeFacet('agg_name', {'buckets': buckets}, 'http://example.com', search_class=self.search_class)

        self.assertEqual(
            {
                'results': expected_results,
                'name': 'Agg_name'
            },
            facet.get_facet()
        )


class HistogramFacetTestCase(TestCase):

    def setUp(self):
        self.search_class = Search()

    def test_get_display_name_with_zero_key(self):
        self.search_class.facets = {
            'agg_name': faceted_search.HistogramFacet(field='agg_field', interval=10)
        }
        self.search_class.facet_display = OrderedDict([
            ('agg_name', 'Agg name')
        ])
        facet = HistogramFacet('agg_name', {}, 'http://example.com', search_class=self.search_class)

        self.assertEqual(
            'Up to 9',
            facet.get_display_name({'key': 0, 'doc_count': 10})
        )

    def test_get_display_name_with_key_and_interval(self):
        self.search_class.facets = {
            'agg_name': faceted_search.HistogramFacet(field='agg_field', interval=40)
        }
        self.search_class.facet_display = OrderedDict([
            ('agg_name', 'Agg name')
        ])
        facet = HistogramFacet('agg_name', {}, 'http://example.com', search_class=self.search_class)

        self.assertEqual(
            '10 to 49',
            facet.get_display_name({'key': 10, 'doc_count': 10})
        )


class FacetsBuilderTestCase(TestCase):

    def setUp(self):
        self.search_class = Search()

    def test_class_uses_correct_facet_type_class(self):
        self.assertIs(
            FacetsBuilder({}, '', search_class=self.search_class).get_facet_class(faceted_search.RangeFacet),
            RangeFacet
        )

        self.assertIs(
            FacetsBuilder({}, '', search_class=self.search_class).get_facet_class(AutoRangeFacet),
            RangeFacet
        )

        self.assertIs(
            FacetsBuilder({}, '', search_class=self.search_class).get_facet_class(faceted_search.HistogramFacet),
            HistogramFacet
        )

    def test_get_facet_class_defaults_to_Facet_if_right_class_not_found(self):
        self.assertIs(
            FacetsBuilder({}, '', search_class=self.search_class).get_facet_class('term'),
            Facet
        )

    def test_sort_facets_sorts_facets_according_to_search_class_facet_display_order(self):
        self.search_class.facet_display = OrderedDict([
            ('first_facet', 'First facet'),
            ('second_facet', 'Second facet')
        ])

        builder = FacetsBuilder({}, '', search_class=self.search_class)

        facets = {
            'second_facet': {},
            'first_facet': {}
        }

        self.assertEqual(
            builder.sort_facets(facets),
            [('first_facet', {}), ('second_facet', {})]
        )

    def test_sort_facets_add_unsorted_facets_last(self):
        self.search_class.facet_display = OrderedDict([
            ('first_facet', 'First facet'),
            ('second_facet', 'Second facet')
        ])

        builder = FacetsBuilder({}, '', search_class=self.search_class)

        facets = {
            'second_facet': {},
            'first_facet': {},
            'third_facet': {},
        }

        self.assertEqual(
            builder.sort_facets(facets),
            [('first_facet', {}), ('second_facet', {}), ('third_facet', {})]
        )

    def test_build_facet_return_value(self):
        self.search_class.facets = {
            'agg_name': TermsFacet(field='agg')
        }
        builder = FacetsBuilder(
            aggs={'agg_name': {'buckets': [{'key': 'Yes', 'doc_count': 12}, {'key': 'No', 'doc_count': 0}]}},
            request_url='http://example.com',
            search_class=self.search_class
        )

        built_facets = {
            'agg_name': {
                'results': [{
                    'name': 'Yes',
                    'count': 12,
                    'show_count': True,
                    'selected': False,
                    'disabled': False,
                    'select_url': 'http://example.com?selected_facets=agg_name%3AYes'
                }, {
                    'name': 'No',
                    'count': 0,
                    'show_count': True,
                    'selected': False,
                    'disabled': True,
                    'select_url': 'http://example.com?selected_facets=agg_name%3ANo'}
                ],
                'name': 'Agg_name'
            }
        }

        self.assertEqual(builder.build_facets(), built_facets)

    def test_build_facets_skips_non_dict_aggs(self):
        self.search_class.facets = {
            'agg_name': TermsFacet()
        }
        builder = FacetsBuilder(
            aggs={'agg_name': {'buckets': [{'key': 'Yes', 'doc_count': 12}, {'key': 'No', 'doc_count': 0}]}, 'non_dict': []},
            request_url='http://example.com',
            search_class=self.search_class
        )

        self.assertNotIn('non_dict', builder.build_facets())
