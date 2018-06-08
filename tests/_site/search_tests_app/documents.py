from django_elasticsearch_dsl import fields as dsl_fields

from oscar.apps.es_search import documents

from .models import SearchModel
from .analyzers import test_analyzer, test_analyzer_2


class SearchDocument(documents.SearchDocument):

    title = dsl_fields.TextField()
    analyzers = [
        test_analyzer,
        test_analyzer_2
    ]
    index_config = {
        "index.requests.cache.enable": True,
        "number_of_shards": 1,
        "number_of_replicas": 0
    }

    class Meta:
        doc_type = 'test_search_doc'
        model = SearchModel
        index = 'test_search_document'
