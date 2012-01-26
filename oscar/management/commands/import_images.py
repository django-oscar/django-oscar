import logging
import sys
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import import_module
import_module('catalogue.utils', ['Importer'], locals())


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
        
        logger = self._get_logger()
        logger.info("Starting image import...")       
        
        dirname = args[0]
        importer = Importer(logger, field=options.get('filename'))
        importer.handle(dirname)
            
    def _get_logger(self):
        logger = logging.getLogger('oscar.apps.image')
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger
            