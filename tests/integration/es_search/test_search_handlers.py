from django.core.paginator import InvalidPage, EmptyPage
from django.http import Http404
from django.test import TestCase
from django_elasticsearch_dsl.test import ESTestCase
from unittest.mock import MagicMock, patch

from tests._site.search_tests_app.search_handlers import SearchHandler


class BaseSearchHandlerTestCase(ESTestCase, TestCase):

    _index_suffixe = ''

    def setUp(self):
        super().setUp()

        self.search_handler = SearchHandler({'q': 'Test'})

    def test_InvalidPage_raised_if_page_num_outside_result_window(self):
        query_class = MagicMock()
        query_class.items_per_page = 50
        query_class.document.index_config = {
            'max_result_window': 100
        }

        self.search_handler.query = query_class

        self.search_handler.get_results({'page': 2})
        with self.assertRaises(InvalidPage):
            self.search_handler.get_results({'page': 3})

    def test_get_results_raises_404_if_page_param_is_not_a_number(self):
        with self.assertRaises(Http404):
            self.search_handler.get_results({'page': ''})

        with self.assertRaises(Http404):
            self.search_handler.get_results({'page': None})

        with self.assertRaises(Http404):
            self.search_handler.get_results({'page': 'Not number'})

    def test_page_number_smaller_than_one_raises_404(self):
        with self.assertRaises(Http404):
            self.search_handler.get_results({'page': 0})

        with self.assertRaises(Http404):
            self.search_handler.get_results({'page': -10})

    def test_invalid_form_raises_404_in_get_results(self):
        self.search_handler.get_results({'page': 1})

        self.search_handler.form.is_valid = MagicMock(return_value=False)
        with self.assertRaises(Http404):
            self.search_handler.get_results({'page': 1})

    def test_get_search_context_data_sets_object_list_on_context_with_given_context_object_name(self):
        ctx = self.search_handler.get_search_context_data('things')

        self.assertEqual(
            ctx['things'],
            self.search_handler.context['page_obj'].object_list
        )

    def test_get_search_kwargs_return_value(self):
        query = 'Test query'
        items_per_page = 20
        page_number = 18
        selected_facets = 'agg_name:agg_value'

        search_handler = SearchHandler({
            'q': query,
            'items_per_page': items_per_page,
            'selected_facets': selected_facets
        })

        search_form = search_handler.form
        search_form.is_valid()

        expected = {
            'query': query,
            'page_number': page_number,
            'max_results': items_per_page,
            'selected_facets': search_form.selected_multi_facets,
            'search_filters': {},
            'sort': search_handler.form.get_sort_params(search_form.cleaned_data)
        }

        self.assertEqual(
            expected,
            self.search_handler.get_search_kwargs(search_form, page_number)
        )

    def test_get_results_returns_the_query_classes_get_search_results(self):
        query_class = MagicMock()
        query_class.items_per_page = 10
        query_class.document.index_config = {
            'max_result_window': 100000
        }

        self.search_handler.query = query_class

        self.search_handler.get_results({'page': 12})

        query_class.assert_called_with(**self.search_handler.get_search_kwargs(self.search_handler.form, 12))

    def test_build_form_adds_the_selected_facets_param_into_the_form_kwarg(self):
        selected_facets = 'agg:value'
        request_data = {'q': 'Test', 'selected_facets': selected_facets}
        search_handler = SearchHandler(request_data)

        form_class_mock = MagicMock()
        search_handler.form_class = form_class_mock

        search_handler.build_form()

        form_class_mock.assert_called_with(search_handler.request_data,
                                           selected_facets=[selected_facets])

    def test_InvalidPage_exception_raised_if_the_paginator_raises_EmptyPage(self):
        self.search_handler.results['paginator'].page = MagicMock(side_effect=EmptyPage)

        with self.assertRaises(InvalidPage):
            self.search_handler.prepare_context(self.search_handler.results)

    def test_prepare_context_return_value_without_results(self):
        query = 'Test query'
        selected_facets = 'agg:value'
        search_handler = SearchHandler({'q': query, 'selected_facets': selected_facets})

        context = {
            'query': query,
            'form': search_handler.form,
            'selected_facets': [selected_facets],
        }

        self.assertEqual(
            context,
            search_handler.prepare_context(None)
        )

    def test_prepare_context_return_value_without_facets(self):
        query = 'Test query'
        selected_facets = 'agg:value'
        search_handler = SearchHandler({'q': query, 'selected_facets': selected_facets, 'page': 1})

        expected_context = {
            'query': query,
            'form': search_handler.form,
            'selected_facets': [selected_facets],
            'paginator': search_handler.results['paginator'],
            'suggestion': search_handler.results['suggestion']
        }

        search_handler.results['facets'] = None

        prepared_context = search_handler.prepare_context(search_handler.results)

        prepare_page_obj = prepared_context.pop('page_obj')
        expected_page_obj = search_handler.results['paginator'].page(1)
        self.assertEqual(prepare_page_obj.number, expected_page_obj.number)
        self.assertEqual(prepare_page_obj.paginator, expected_page_obj.paginator)
        self.assertEqual(prepare_page_obj.object_list, expected_page_obj.object_list)

        self.assertEqual(
            expected_context,
            prepared_context
        )

    def test_prepare_context_return_value(self):
        query = 'Test query'
        selected_facets = 'agg:value'
        search_handler = SearchHandler({'q': query, 'selected_facets': selected_facets, 'page': 1})
        search_handler.results['facets'] = {'dummy': 'facets'}
        search_handler.results['suggestion'] = 'New suggestion'

        facet_data = {
            'agg_name': {
                'results': [{}, {}],
                'name': 'Agg_name'
            }
        }

        expected_context = {
            'query': query,
            'form': search_handler.form,
            'selected_facets': [selected_facets],
            'paginator': search_handler.results['paginator'],
            'suggestion': search_handler.results['suggestion'],
            'facet_data': facet_data,
            'has_facets': True
        }

        with patch('oscar.apps.es_search.search_handlers.FacetsBuilder.build_facets', return_value=facet_data):
            prepared_context = search_handler.prepare_context(search_handler.results)
            prepared_context.pop('page_obj')

            self.assertEqual(
                expected_context,
                prepared_context
            )

    def test_has_facets_set_to_False_if_all_results_are_empty(self):
        search_handler = SearchHandler({'q': 'Test'})
        search_handler.results['facets'] = {'dummy': 'facets'}

        facet_data = {
            'agg_1': {
                'results': []
            },
            'agg_2': {
                'results': []
            }
        }

        with patch('oscar.apps.es_search.search_handlers.FacetsBuilder.build_facets', return_value=facet_data):
            prepared_context = search_handler.prepare_context(search_handler.results)

            self.assertFalse(
                prepared_context['has_facets']
            )
