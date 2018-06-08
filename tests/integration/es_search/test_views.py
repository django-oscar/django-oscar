from unittest.mock import patch, MagicMock

from django.core.paginator import InvalidPage
from django.test import TestCase

from oscar.apps.es_search.views import BaseSearchView, BaseAutoSuggestView

from oscar.test.utils import RequestFactory


class BaseSearchViewTestCase(TestCase):

    def test_remove_page_arg(self):
        url = '/search/products/?page=10&query=test'

        self.assertEqual(
            '/search/products/?query=test',
            BaseSearchView.remove_page_arg(url)
        )

    @patch.object(BaseSearchView, 'get_search_handler', side_effect=InvalidPage)
    def test_get_redirects_to_same_page_with_Page_param_removed_if_page_was_invalid(self, get_search_handler_mock):
        request = RequestFactory().get('/search/?page=94')

        view = BaseSearchView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/search/')

    @patch.object(BaseSearchView, 'get_search_handler')
    def test_get_sends_search_signal_if_succesful(self, get_search_handler_mock):
        query = 'test query'
        search_handler = MagicMock()
        search_handler.form.cleaned_data = {'q': query}

        get_search_handler_mock.return_value = search_handler

        search_signal_mock = MagicMock()

        class SearchView(BaseSearchView):
            template_name = ''
            search_signal = search_signal_mock

        request = RequestFactory().get('/search/?query={}'.format(query))

        view = SearchView.as_view()
        view(request)

        self.assertTrue(search_signal_mock.send.called)

        args, kwargs = search_signal_mock.send.call_args

        self.assertEqual(
            kwargs['session'],
            request.session
        )
        self.assertEqual(
            kwargs['user'],
            request.user
        )
        self.assertEqual(
            kwargs['query'],
            query
        )
        self.assertIsInstance(
            kwargs['sender'],
            SearchView
        )

    def test_get_search_handler_return_search_handler_class_instance_with_get_params_and_request_path(self):
        request = RequestFactory().get('/full/path/?some=params')

        class SearchView(BaseSearchView):
            search_handler_class = MagicMock()
            search_signal = MagicMock()
            template_name = ''

        view = SearchView.as_view()
        view(request)

        SearchView.search_handler_class.assert_called_with(request.GET, request.get_full_path())


class AutoSuggestView(BaseAutoSuggestView):
    query_class = MagicMock()
    form_class = MagicMock()


class BaseAutoSuggestViewTestCase(TestCase):

    def test_get_query(self):
        query = 'Test query'

        form = MagicMock()
        form.cleaned_data = {'q': query}

        view = AutoSuggestView()
        view.get_query(form)

        AutoSuggestView.query_class.assert_called_with(**view.get_query_kwargs(form))

    def test_get_query_kwargs(self):
        query = 'Test query'

        form = MagicMock()
        form.cleaned_data = {'q': query}

        self.assertEqual(
            AutoSuggestView().get_query_kwargs(form),
            {
                'query': query
            }
        )

    @patch('oscar.apps.es_search.views.JsonResponse')
    def test_successful_get_response(self, JsonResponseMock):
        query_instance = MagicMock()
        with patch.object(AutoSuggestView, 'get_query', return_value=query_instance):
            view = AutoSuggestView.as_view()
            response = view(RequestFactory().get('/'))

            self.assertEqual(
                response,
                JsonResponseMock(query_instance.get_suggestions(), safe=False)
            )

            JsonResponseMock.assert_called_with(query_instance.get_suggestions(), safe=False)

    @patch('oscar.apps.es_search.views.JsonResponse')
    def test_failed_response(self, JsonResponseMock):
        form = MagicMock()
        form.is_valid.return_value = False

        class AutoSuggestView(BaseAutoSuggestView):
            query_class = MagicMock()
            form_class = MagicMock(return_value=form)

        view = AutoSuggestView.as_view()
        view(RequestFactory().get('/'))
        JsonResponseMock.assert_called_with([], safe=False, status=400)
