from django.conf import settings
from django.core.management.base import BaseCommand

from django_elasticsearch_dsl.registries import registry

from ...registries import AnalyzerRegistry


class Command(BaseCommand):
    help = "Completely rebuilds the search index by removing the old data and then updating."

    def handle(self, **options):
        for index in registry.get_indices():
            index.delete(ignore=404)

            self.stdout.write("Creating index '{}'".format(index))

            analyzer_registry = AnalyzerRegistry()
            analyzer_registry.define_in_index(index)

            index.settings(**settings.OSCAR_SEARCH['INDEX_CONFIG'])
            index.create()

        for Document in registry.get_documents():
            doc = Document()
            qs = doc.get_queryset()
            self.stdout.write("Indexing {} '{}' objects".format(
                qs.count(), doc._doc_type.model.__name__)
            )
            doc.update(qs.iterator())
