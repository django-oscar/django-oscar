import logging

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_class

CatalogueImporter = get_class('partner.importers', 'CatalogueImporter')
ImportingError = get_class('partner.exceptions', 'ImportingError')

logger = logging.getLogger('oscar.catalogue.import')


class Command(BaseCommand):
    help = 'For creating product catalogues based on a CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', nargs='+',
            help='/path/to/file1.csv /path/to/file2.csv ...')
        parser.add_argument(
            '--flush',
            action='store_true',
            dest='flush',
            default=False,
            help='Flush tables before importing')
        parser.add_argument(
            '--delimiter',
            dest='delimiter',
            default=",",
            help='Delimiter used within CSV file(s)')

    def handle(self, *args, **options):
        logger.info("Starting catalogue import")
        importer = CatalogueImporter(
            logger, delimiter=options.get('delimiter'),
            flush=options.get('flush'))
        for file_path in options['filename']:
            logger.info(" - Importing records from '%s'" % file_path)
            try:
                importer.handle(file_path)
            except ImportingError as e:
                raise CommandError(str(e))
