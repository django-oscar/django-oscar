from oscar.apps.es_search.forms import BaseSearchForm
from oscar.apps.es_search.search_handlers import BaseSearchHandler

from oscar.test.utils import RequestFactory
from .search import Search


class SearchHandler(BaseSearchHandler):

    form_class = BaseSearchForm
    query = Search

    def __init__(self, form_data=None, *args, **kwargs):
        form_data = form_data or {}
        request = RequestFactory().post('/', data=form_data)
        super(SearchHandler, self).__init__(request.POST, '/')
