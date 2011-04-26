import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import import_module
import_module('catalogue_import.utils', ['Importer'], locals())
import_module('catalogue_import.exceptions', ['CatalogueImportException'], locals())


class Command(BaseCommand):
    
    args = '/path/to/file1.csv /path/to/file2.csv ...'
    help = 'For creating product catalogues based on a CSV file'
    
    option_list = BaseCommand.option_list + (
        make_option('--flush',
            action='store_true',
            dest='flush',
            default=False,
            help='Flush tables before importing'),
        make_option('--delimiter',
            dest='delimiter',
            default=",",
            help='Delimiter used within CSV file(s)'),
        )

    def handle(self, *args, **options):
        logger = self._get_logger()
        logger.info("Starting catalogue import")
        importer = Importer(logger, delimiter=options.get('delimiter'), flush=options.get('flush'))
        for file_path in args:
            logger.info(" - Importing records from '%s'" % file_path)
            try:
                importer.handle(file_path)
            except CatalogueImportException, e:
                raise CommandError(str(e))
            
    def _get_logger(self):
        logger = logging.getLogger('oscar.apps.catalogue_import')
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger
        
        
        
            