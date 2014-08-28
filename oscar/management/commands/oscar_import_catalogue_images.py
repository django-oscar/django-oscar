import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_class

Importer = get_class('catalogue.utils', 'Importer')

logger = logging.getLogger('oscar.catalogue.import')


class Command(BaseCommand):
    args = '/path/to/folder'
    help = 'For importing product images from a folder'

    option_list = BaseCommand.option_list + (
        make_option('--filename',
                    dest='filename',
                    default='upc',
                    help='Product field to lookup from image filename'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Command requires a path to a single folder')

        logger.info("Starting image import")
        dirname = args[0]
        importer = Importer(logger, field=options.get('filename'))
        importer.handle(dirname)
