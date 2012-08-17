import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_class
CatalogueImporter = get_class('partner.utils', 'CatalogueImporter')
CatalogueImportError = get_class('partner.exceptions', 'CatalogueImportError')


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
        if not args:
            raise CommandError("Please select a CSV file to import")

        logger.info("Starting catalogue import")
        importer = CatalogueImporter(logger,
                                     delimiter=options.get('delimiter'),
                                     flush=options.get('flush'))
        for file_path in args:
            logger.info(" - Importing records from '%s'" % file_path)
            try:
                importer.handle(file_path)
            except CatalogueImportError, e:
                raise CommandError(str(e))

    def _get_logger(self):
        logger = logging.getLogger(__file__)
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger
