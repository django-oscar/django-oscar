import logging
import sys
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import import_module
import_module('partner.utils', ['Importer'], locals())
import_module('partner.exceptions', ['StockImportException'], locals())

class Command(BaseCommand):
    
    args = 'partner /path/to/file1.csv'
    help = 'For updating stock for a partner based on a CSV file'
    
    option_list = BaseCommand.option_list + (
        make_option('--delimiter',
            dest='delimiter',
            default=",",
            help='Delimiter used within CSV file(s)'),
        )

    def handle(self, *args, **options):
        logger = self._get_logger()

        if len(args) != 2:
            raise CommandError('Command requires a partner and a path to a csv file') 
        
        logger.info("Starting stock import")
        importer = Importer(logger, partner=args[0], delimiter=options.get('delimiter'))
        
        logger.info(" - Importing records from '%s'" % args[1])
        try:
            importer.handle(args[1])
        except StockImportException, e:
            raise CommandError(str(e))
            
    def _get_logger(self):
        logger = logging.getLogger('oscar.apps.partner')
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger