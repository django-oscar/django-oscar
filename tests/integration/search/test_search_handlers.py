from copy import deepcopy
from django.conf import settings
from django.core.paginator import InvalidPage
from django.test import override_settings
from django_elasticsearch_dsl.test import ESTestCase
from oscar.test.utils import RequestFactory

from oscar.apps.search.forms import BaseSearchForm
from oscar.apps.search.search_handlers import BaseSearchHandler

from tests._site.search_tests_app.search import Search


class TestSearchHandler(BaseSearchHandler):

    form_class = BaseSearchForm
    query = Search

    def __init__(self, form_data=None):
        form_data = form_data or {}
        request = RequestFactory().post('/', data=form_data)
        super(TestSearchHandler, self).__init__(request.POST, '/')


class BaseSearchHandlerTestCase(ESTestCase):

    def test_InvalidPage_raised_if_page_num_outside_result_window(self):
        OSCAR_SEARCH = deepcopy(settings.OSCAR_SEARCH.copy())
        OSCAR_SEARCH['INDEX_CONFIG']['max_result_window'] = 100

        with override_settings(OSCAR_PRODUCTS_PER_PAGE=50, OSCAR_SEARCH=OSCAR_SEARCH):
            search_handler = TestSearchHandler({'q': 'Test'})

            search_handler.get_results({'page': 2})
            with self.assertRaises(InvalidPage):
                search_handler.get_results({'page': 3})
