import logging

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_class

CatalogueImporter = get_class('partner.importers', 'CatalogueImporter')
CatalogueImportError = get_class('partner.exceptions', 'CatalogueImportError')

logger = logging.getLogger('oscar.catalogue.import')


class Command(BaseCommand):
    args = '/path/to/file1.csv /path/to/file2.csv ...'
    help = 'For creating product catalogues based on a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('/path/to/file.csv', nargs='+')

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
        for file_path in options['/path/to/file.csv']:
            logger.info(" - Importing records from '%s'" % file_path)
            try:
                importer.handle(file_path)
            except CatalogueImportError as e:
                raise CommandError(str(e))
