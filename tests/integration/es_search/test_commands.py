from django.db import models
from django.test import TestCase
from django_elasticsearch_dsl import DocType

from unittest.mock import MagicMock, patch, call

from oscar.apps.es_search.management.commands.update_oscar_index import Command as UpdateOscarIndexCommand

from tests._site.search_tests_app.documents import SearchDocument
from tests._site.search_tests_app.models import SearchModel


class UpdateOscarIndexTestCase(TestCase):

    def test_update_documents_calls_Document_update_on_the_Documents_queryset(self):
        class Model(models.Model):
            class Meta:
                app_label = 'model'

        class Doc(DocType):
            class Meta:
                model = Model

        qs = MagicMock()
        Doc.get_queryset = MagicMock(return_value=qs)
        Doc.update = MagicMock()

        updater = UpdateOscarIndexCommand()
        updater.stdout = MagicMock()
        updater.update_document(Doc)

        Doc.update.assert_called_with(qs.iterator())

    @patch('oscar.apps.es_search.management.commands.update_oscar_index.Index')
    def test_document_build_index_not_called_if_rebuild_arg_not_passed_and_index_already_created(self, IndexMock):
        index = IndexMock.return_value
        index.exists.return_value = True

        doc = SearchDocument
        with patch('oscar.apps.es_search.management.commands.update_oscar_index.registry.get_documents',
                   return_value=[doc]):
            with patch.object(SearchDocument, 'build_index') as build_index_mock:
                cmd = UpdateOscarIndexCommand()
                cmd.handle(rebuild=False, models='')

                self.assertFalse(build_index_mock.called)

    @patch('oscar.apps.es_search.management.commands.update_oscar_index.Index')
    def test_document_build_index_called_if_rebuild_arg_passed(self, IndexMock):
        index = IndexMock.return_value
        index.exists.return_value = True

        doc = SearchDocument
        with patch('oscar.apps.es_search.management.commands.update_oscar_index.registry.get_documents',
                   return_value=[doc]):
            with patch.object(SearchDocument, 'build_index') as build_index_mock:
                cmd = UpdateOscarIndexCommand()
                cmd.handle(rebuild=True, models='')

                self.assertTrue(build_index_mock.called)

    @patch('oscar.apps.es_search.management.commands.update_oscar_index.Index')
    def test_document_build_index_called_if_index_doesnt_already_exist(self, IndexMock):
        index = IndexMock.return_value
        index.exists.return_value = False

        doc = SearchDocument
        with patch('oscar.apps.es_search.management.commands.update_oscar_index.registry.get_documents',
                   return_value=[doc]):
            with patch.object(SearchDocument, 'build_index') as build_index_mock:
                cmd = UpdateOscarIndexCommand()
                cmd.handle(rebuild=False, models='')

                self.assertTrue(build_index_mock.called)

    def test_update_documents_called_in_update_command(self):
        doc = SearchDocument
        with patch('oscar.apps.es_search.management.commands.update_oscar_index.registry.get_documents',
                   return_value=[doc]):
            with patch.object(UpdateOscarIndexCommand, 'update_document') as update_doc_mock:
                cmd = UpdateOscarIndexCommand()
                cmd.handle(rebuild=False, models='')

                update_doc_mock.assert_has_calls([call(doc)])

    def test_fetch_models_fetches_models_from_provided_paths(self):
        self.assertEqual(
            UpdateOscarIndexCommand().fetch_models(['search_tests_app.searchmodel']),
            [SearchModel]
        )

    def test_fetch_models_fails_with_error_if_unable_to_find_model_from_provided_path(self):
        cmd = UpdateOscarIndexCommand()
        cmd.stderr = MagicMock()

        self.assertIsNone(
            cmd.fetch_models(['search_tests_app.nonexsitentmodel'])
        )

        cmd.stderr.write.called_with('Could not find model search_tests_app.nonexsitentmodel')
