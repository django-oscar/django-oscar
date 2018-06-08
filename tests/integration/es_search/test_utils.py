from django.test import TestCase
from elasticsearch_dsl import HistogramFacet, RangeFacet, TermsFacet
from elasticsearch_dsl.query import Range, Term, Q
from unittest.mock import MagicMock, patch

from oscar.apps.es_search import utils
from oscar.apps.es_search.utils import PaginatedObjectList, ESPaginator


class SearchUtilsTestCase(TestCase):

    def test_terms_buckets_to_values_list(self):
        buckets = [
            {
                "key": 5,
                "doc_count": 12
            },
            {
                "key": 15,
                "doc_count": 5
            },
            {
                "key": 25,
                "doc_count": 9
            }
        ]

        # should have twelve 5s, five 15s and nine 25s
        expected_results = [
            5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
            15, 15, 15, 15, 15,
            25, 25, 25, 25, 25, 25, 25, 25, 25
        ]

        self.assertEqual(utils.terms_buckets_to_values_list(buckets), expected_results)

    def test_chunks_splits_given_list_into_multiple_lists_each_containing_the_given_number_of_values(self):
        values = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10]

        self.assertEqual(
            list(utils.chunks(values, 3)),
            [
                [1, 1, 2],
                [2, 3, 3],
                [4, 4, 5],
                [5, 6, 6],
                [7, 7, 8],
                [8, 9, 9],
                [10, 10]
            ]
        )

        self.assertEqual(
            list(utils.chunks(values, 4)),
            [
                [1, 1, 2, 2],
                [3, 3, 4, 4],
                [5, 5, 6, 6],
                [7, 7, 8, 8],
                [9, 9, 10, 10]
            ]
        )

        self.assertEqual(
            list(utils.chunks(values, 5)),
            [
                [1, 1, 2, 2, 3],
                [3, 4, 4, 5, 5],
                [6, 6, 7, 7, 8],
                [8, 9, 9, 10, 10]
            ]
        )

    def test_agg_terms_to_filters(self):
        agg = TermsFacet(field='title')

        self.assertEqual(
            utils.agg_terms_to_filters(agg, ['First title']),
            [Term(title='First title')]
        )

        self.assertEqual(
            utils.agg_terms_to_filters(agg, ['First title', 'Second title']),
            [Term(title='First title'), Term(title='Second title')]
        )

    def test_agg_histogram_to_filters(self):
        agg = HistogramFacet(field='size', interval=10)

        self.assertEqual(
            utils.agg_histogram_to_filters(agg, ['10']),
            [Range(size={'gte': '10', 'lt': 20})]
        )

        self.assertEqual(
            utils.agg_histogram_to_filters(agg, ['10', '20']),
            [Range(size={'gte': '10', 'lt': 20}), Range(size={'gte': '20', 'lt': 30})]
        )

    def test_agg_to_filter_raises_NotImplementedError_if_given_agg_type_is_unknown(self):
        class UnknownFacet(object):
            pass

        agg = UnknownFacet()

        with self.assertRaises(NotImplementedError):
            utils.agg_to_filter(agg, ['Value'])

    def test_agg_to_filter_returns_empty_query_if_no_values_given(self):
        agg = TermsFacet(field='Title')

        self.assertEqual(
            utils.agg_to_filter(agg, []),
            Q()
        )

    def test_agg_to_filter_ORs_filters_to_each_other(self):
        agg = TermsFacet(field='title')

        self.assertEqual(
            utils.agg_to_filter(agg, ['First', 'Second']),
            Term(title='First') | Term(title='Second')
        )

    def test_agg_to_filter_accepts_non_list_value(self):
        agg = TermsFacet(field='title')

        self.assertEqual(
            utils.agg_to_filter(agg, 'First'),
            Term(title='First')
        )

    def test_agg_range_to_filters(self):
        agg = RangeFacet(field='size', ranges=[])

        self.assertEqual(
            utils.agg_range_to_filters(agg, ['10-30']),
            [Range(size={'gte': 10.0, 'lte': 30.0})]
        )

        self.assertEqual(
            utils.agg_range_to_filters(agg, ['-30']),
            [Range(size={'lte': 30.0})]
        )

        self.assertEqual(
            utils.agg_range_to_filters(agg, ['10-']),
            [Range(size={'gte': 10.0})]
        )

    def test_agg_range_to_filters_skips_values_not_seperated_by_dash(self):
        agg = RangeFacet(field='size', ranges=[])

        self.assertEqual(
            utils.agg_range_to_filters(agg, ['10-30', 'adlc', '10-200']),
            [Range(size={'gte': 10.0, 'lte': 30.0}), Range(size={'gte': 10.0, 'lte': 200.0})]
        )

    def test_get_auto_ranges_generates_range_dict_with_to_from_and_doc_count(self):
        chunks = [[1, 2], [3, 4]]
        self.assertEqual(
            utils.get_auto_ranges(chunks),
            [
                {'from': 0, 'to': 2, 'doc_count': 2},
                {'from': 3, 'to': 4, 'doc_count': 2}
            ]
        )

    def test_get_auto_ranges_uses_the_first_chunks_range_end_without_rounding_if_less_than_10(self):
        chunks = [[1, 3], [10, 20]]

        self.assertEqual(
            utils.get_auto_ranges(chunks),
            [
                {'from': 0, 'to': 3, 'doc_count': 2},
                {'from': 4, 'to': 20, 'doc_count': 2}
            ]
        )

    def test_get_auto_ranges_CEILs_to_the_next_tenth_for_values_above_10_and_below_100(self):
        chunks = [[23, 33], [45, 67]]

        self.assertEqual(
            utils.get_auto_ranges(chunks),
            [
                {'from': 0, 'to': 40, 'doc_count': 2},
                {'from': 41, 'to': 70, 'doc_count': 2}
            ]
        )

    def test_get_auto_ranges_CEILs_to_the_next_multiple_of_power_of_10_for_values_above_100(self):
        chunks = [[23, 33], [120, 260]]

        self.assertEqual(
            utils.get_auto_ranges(chunks),
            [
                {'from': 0, 'to': 40, 'doc_count': 2},
                {'from': 41, 'to': 300, 'doc_count': 2}
            ]
        )

    def test_get_auto_ranges_includes_values_into_previous_group_if_they_are_smaller_or_equal_to_previous_range_end(self):
        chunks = [[23, 33], [33, 34], [51, 65], [64, 62]]

        self.assertEqual(
            utils.get_auto_ranges(chunks),
            [
                {'from': 0, 'to': 40, 'doc_count': 4},
                {'from': 41, 'to': 70, 'doc_count': 4}
            ]
        )

    def test_get_auto_ranges_CEILs_to_the_next_10th_if_values_are_larger_than_100_but_closely_spread_out(self):
        chunks = [[900, 901], [901, 901], [902, 902], [902, 903]]

        self.assertEqual(
            utils.get_auto_ranges(chunks),
            [
                {'from': 0, 'to': 910, 'doc_count': 8},
            ]
        )


class PaginatedObjectListTestCase(TestCase):

    def test_count_returns_total(self):
        obj = PaginatedObjectList([], 100)

        self.assertEqual(
            obj.count(),
            obj.total
        )

    def test_iterating_over_PaginatedObjectList_iterates_over_defined_object_list(self):
        lst = [1, 2, 3, 4]

        obj = PaginatedObjectList(lst, 4)

        self.assertEqual(
            list(obj.__iter__()),
            lst
        )


class ESPaginatorTestCase(TestCase):

    def test_page_returns_the_object_list_as_is_without_slicing(self):
        object_list = MagicMock()
        object_list.count = MagicMock(return_value=30)

        paginator = ESPaginator(object_list, per_page=5)
        paginator.page(2)

        object_list.__getitem__.assert_not_called()

    def test_page_number_validated(self):
        object_list = MagicMock()
        object_list.count = MagicMock(return_value=30)

        validated_number = MagicMock()
        with patch.object(ESPaginator, 'validate_number', return_value=validated_number) as validate_mock:
            with patch('oscar.apps.es_search.utils.Page') as PageMock:
                paginator = ESPaginator(object_list, per_page=5)
                paginator.page(2)

                validate_mock.assert_called_with(2)

                PageMock.assert_called_with(object_list, validate_mock.return_value, paginator)
