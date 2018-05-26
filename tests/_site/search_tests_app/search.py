from oscar.apps.search.search import BaseSearch, BaseAutoSuggestSearch

from .documents import SearchDocument


class Search(BaseSearch):

    document = SearchDocument
    settings_key = 'TEST_SEARCH'


class AutoSuggestSearch(Search, BaseAutoSuggestSearch):

    source_fields = ['title']
