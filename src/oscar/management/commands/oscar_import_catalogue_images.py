import logging

from django.core.management.base import BaseCommand

from oscar.core.loading import get_class

Importer = get_class('catalogue.utils', 'Importer')

logger = logging.getLogger('oscar.catalogue.import')


class Command(BaseCommand):
    help = 'For importing product images from a folder'

    def add_arguments(self, parser):
        parser.add_argument('path', help='/path/to/folder')

        parser.add_argument(
            '--filename',
            dest='filename',
            default='upc',
            help='Product field to lookup from image filename')

    def handle(self, *args, **options):
        logger.info("Starting image import")
        dirname = options['path']
        importer = Importer(logger, field=options.get('filename'))
        importer.handle(dirname)
