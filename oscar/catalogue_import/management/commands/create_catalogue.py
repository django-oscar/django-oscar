import logging
import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from oscar.services import import_module

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

log = logging.getLogger('catalogue_import')
formatter = logging.Formatter(LOGGING_FORMAT)
stream = logging.StreamHandler(sys.stderr)
stream.setLevel(logging.INFO)
stream.setFormatter(formatter)
log.addHandler(stream)
log.setLevel(LOGGING_LEVEL)

catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
catalogue_exception = import_module('catalogue_import.exceptions', ['CatalogueImportException'])

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--flush',
            action='store_true',
            dest='flush',
            default=False,
            help='Flush tables before importing'),
        make_option('--csv-type',
            type='string',
            dest='csv_type',
            nargs=1,
            default='simple',
            help='CSV content type'),
        make_option('--file',
            type='string',
            dest='filename',
            nargs=1,
            default=None,
            help='/path/to/file'),
        )


    def handle(self, *args, **options):
        importer = catalogue_import.CatalogueImport()
        importer.flush = options.get('flush')
        importer.csv_type = options.get('csv_type')
        importer.file = options.get('filename')
        try:
            importer.handle()
        except catalogue_exception.CatalogueImportException as e:
            self.error(e)
            
    def error(self, message):
        log.error(message)
        sys.exit(0)
            