from oscar.apps.es_search.search import BaseSearch, BaseAutoSuggestSearch

from .documents import SearchDocument


class Search(BaseSearch):

    document = SearchDocument
    settings_key = 'TEST_SEARCH'
    query_config = {
        "query_type": "multi_match",
        "fields": ["title"],
        "minimum_should_match": "70%",
    }


class AutoSuggestSearch(Search, BaseAutoSuggestSearch):

    source_fields = ['title']
