import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import import_module
import_module('catalogue_import.utils', ['Importer'], locals())
import_module('catalogue_import.exceptions', ['CatalogueImportException'], locals())

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

log = logging.getLogger('oscar.apps.catalogue_import')
formatter = logging.Formatter(LOGGING_FORMAT)
stream = logging.StreamHandler(sys.stderr)
stream.setLevel(logging.INFO)
stream.setFormatter(formatter)
log.addHandler(stream)
log.setLevel(LOGGING_LEVEL)


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--flush',
            action='store_true',
            dest='flush',
            default=False,
            help='Flush tables before importing'),
        make_option('--file',
            type='string',
            dest='filename',
            nargs=1,
            default=None,
            help='/path/to/file'),
        )

    def handle(self, *args, **options):
        importer = Importer()
        importer.flush = options.get('flush')
        importer.afile = options.get('filename')
        try:
            importer.handle()
        except CatalogueImportException as e:
            self.error(e)
            
    def error(self, message):
        log.error(message)
        sys.exit(0)
            