import logging
import sys
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import import_module
import_module('image.utils', ['Importer'], locals())
import_module('image.exceptions', ['ImageImportException'], locals())


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
        logger = self._get_logger()
        logger.info("Starting image import...")

        if len(args) != 1:
            raise CommandError('Command requires a path to a single folder')        
        
        dirname = args[0]
        
        all_files = [f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname,f))]
        
        importer = Importer(logger, field=options.get('filename'))
        
        for f in all_files:
            ext = os.path.splitext(f)[1]
            if ext in ['.jpeg','.jpg','.gif','.png']:
                try:
                    importer.handle(f,dirname)
                except ImageImportException, e:
                    raise CommandError(str(e))
            
    def _get_logger(self):
        logger = logging.getLogger('oscar.apps.image')
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger
            