import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.apps.partner.importers import DemoSiteImporter


class Command(BaseCommand):
    args = '/path/to/file1.csv /path/to/file2.csv ...'
    help = 'For creating product catalogues based on a CSV file'

    option_list = BaseCommand.option_list + (
        make_option('--class', dest='product_class',
                    help='Product class'),)

    def handle(self, *args, **options):
        logger = self._get_logger()
        if not args:
            raise CommandError("Please select a CSV file to import")

        product_class = options['product_class']
        if not product_class:
            raise CommandError("Please specify a product class name")

        logger.info("Starting %s catalogue import", product_class)
        importer = DemoSiteImporter(logger)
        for file_path in args:
            logger.info(" - Importing records from '%s'" % file_path)
            importer.handle(product_class, file_path)

    def _get_logger(self):
        logger = logging.getLogger(__file__)
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger
