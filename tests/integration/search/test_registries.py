import mock

from django.conf import settings
from django.test import TestCase
from django_elasticsearch_dsl import Index

from oscar.apps.search.registries import AnalyzerRegistry

from tests._site.apps.myapp.analyzers import test_analyzer


class AnalyzerRegistryTestCase(TestCase):

    def test_raises_error_if_trying_to_register_analyzer_with_registered_name(self):
        settings.OSCAR_SEARCH['ANALYZERS'] = [
            'tests._site.apps.myapp.analyzers.test_analyzer',
            'tests._site.apps.myapp.analyzers.test_analyzer_2'
        ]
        analyzer_registry = AnalyzerRegistry()
        index = Index('test')
        with self.assertRaises(KeyError):
            analyzer_registry.define_in_index(index)

    def test_define_in_index_finds_analyzers_in_analyzer_dot_py_files(self):
        settings.OSCAR_SEARCH['ANALYZERS'] = ['tests._site.apps.myapp.analyzers.test_analyzer']

        with mock.patch.object(Index, 'analyzer') as mock_analyzer:
            index = Index('test')

            analyzer_registry = AnalyzerRegistry()
            analyzer_registry.define_in_index(index)

            mock_analyzer.assert_called_with(test_analyzer)
