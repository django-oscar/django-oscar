from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from oscar.apps.es_search.documents import SearchDocument

from tests._site.search_tests_app.models import SearchModel
from tests._site.search_tests_app.documents import SearchDocument as TestSearchDocument


class SearchDocTypeMetaTestCase(TestCase):

    def test_index_name_prefixed_with_OSCAR_SEARCH_INDEX_PREFIX_setting(self):
        with override_settings(OSCAR_SEARCH={'INDEX_PREFIX': 'test_prefix'}):
            class TestSearch(SearchDocument):
                class Meta:
                    index = 'search_index'
                    model = SearchModel

            self.assertEqual(TestSearch.index, 'test_prefix--search_index')

    def test_index_name_generated_from_model_name_if_none_supplied(self):
        with override_settings(OSCAR_SEARCH={'INDEX_PREFIX': 'test_prefix'}):
            class TestSearch(SearchDocument):
                class Meta:
                    model = SearchModel

            self.assertEqual(TestSearch.index, 'test_prefix--searchmodel')

    def test_index_and_doc_type_properties_set_on_SearchDocument_classes(self):
        with override_settings(OSCAR_SEARCH={'INDEX_PREFIX': 'test_prefix'}):
            class TestSearch(SearchDocument):
                class Meta:
                    doc_type = 'search_doc_type'
                    index = 'search_index'
                    model = SearchModel

            self.assertEqual(TestSearch.index, 'test_prefix--search_index')
            self.assertEqual(TestSearch.doc_type, 'search_doc_type')


class SearchDocumentTestCase(TestCase):

    @patch('oscar.apps.es_search.documents.Index')
    def test_build_index_deletes_existing_index(self, IndexMock):
        index = IndexMock.return_value

        TestSearchDocument.build_index()

        index.delete.assert_called_with(ignore=404)

    def test_analyzers_defined_for_index_in_define_analyzers(self):
        index = MagicMock()
        TestSearchDocument.define_analyzers(index)

        for analyzer in TestSearchDocument.analyzers:
            index.analyzer.assert_called_with(analyzer)

    @patch('oscar.apps.es_search.documents.Index')
    def test_define_analyzers_called_in_build_index(self, IndexMock):
        with patch.object(TestSearchDocument, 'define_analyzers') as define_analyzers_mock:
            TestSearchDocument.build_index()

            self.assertTrue(define_analyzers_mock.called)

    @patch('oscar.apps.es_search.documents.Index')
    def test_document_index_configured_from_documents_config(self, IndexMock):
        index = IndexMock.return_value

        TestSearchDocument.build_index()

        index.settings.assert_called_with(**TestSearchDocument.index_config)

    @patch('oscar.apps.es_search.documents.Index')
    def test_index_create_called_in_build_index(self, IndexMock):
        index = IndexMock.return_value

        TestSearchDocument.build_index()

        self.assertTrue(index.create.called)
