from django.core.management.base import BaseCommand

from django_elasticsearch_dsl.indices import Index
from django_elasticsearch_dsl.registries import registry
from oscar.core.loading import get_model


class Command(BaseCommand):
    help = "Update documents and their indices."

    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild',
            action='store_true',
            dest='rebuild',
            help="Rebuild the documents' indices"
        )
        parser.add_argument(
            'models',
            nargs='*',
            type=str,
            help="Model paths for models whose documents you want to update e.g `catalogue.Product`"
                 "to update product model's document.",
            default=''
        )

    def update_document(self, Document):
        doc = Document()
        qs = doc.get_queryset()
        self.stdout.write("Indexing {} '{}' objects".format(
            qs.count(), doc._doc_type.model.__name__)
        )
        doc.update(qs.iterator())

    def fetch_models(self, model_paths):
        models = []
        if model_paths:
            for path in model_paths:
                try:
                    models.append(get_model(*path.split('.')))
                except LookupError:
                    self.stderr.write('Could not find model {}'.format(path))

        return models or None

    def handle(self, *args, **options):
        models = self.fetch_models(options['models'])

        for Document in registry.get_documents(models):
            document_index = Index(Document.index)
            # rebuild the index if --rebuild arg passed or if the index had not been created
            if options['rebuild'] or not document_index.exists():
                self.stdout.write("Creating index '{}'".format(Document.index))
                Document.build_index()
            self.update_document(Document)
