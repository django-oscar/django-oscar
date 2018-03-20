from django.core.management.base import BaseCommand

from django_elasticsearch_dsl.registries import registry


class Command(BaseCommand):
    help = "Completely rebuilds the search index by removing the old data and then updating."

    def handle(self, **options):
        for Document in registry.get_documents():
            doc = Document()
            qs = doc.get_queryset()
            self.stdout.write("Updating {} '{}' objects".format(
                qs.count(), doc._doc_type.model.__name__)
            )
            doc.update(qs.iterator(), refresh=True)
