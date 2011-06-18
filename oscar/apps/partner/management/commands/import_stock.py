import logging
import sys
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import import_module
import_module('partner.utils', ['StockImporter'], locals())
import_module('partner.exceptions', ['ImportError'], locals())


class Command(BaseCommand):
    
    args = '<partner> /path/to/file1.csv'
    help = 'For updating stock for a partner based on a CSV file'
    
    option_list = BaseCommand.option_list + (
        make_option('--delimiter',
            dest='delimiter',
            default=",",
            help='Delimiter used within CSV file(s)'),
        )

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError('Command requires a partner and a path to a csv file') 
        
        logger = self._get_logger()
        
        try:
            importer = StockImporter(logger, partner=args[0], delimiter=options.get('delimiter'))
            logger.info("Starting stock import")
            logger.info(" - Importing records from '%s'" % args[1])
            importer.handle(args[1])
        except ImportError, e:
            raise CommandError(str(e))
            
    def _get_logger(self):
        logger = logging.getLogger('oscar.apps.partner.import_stock')
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger