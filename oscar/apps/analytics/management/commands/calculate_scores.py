import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from oscar.apps.analytics.models import ProductRecord
from oscar.apps.catalogue.models import Item


class Command(BaseCommand):
    
    help = 'For creating product catalogues based on a CSV file'
    
    def handle(self, *args, **options):
        
        logger = self._get_logger()
        cursor = connection.cursor()
        
        logger.info("Calculating product scores")
        sql = '''UPDATE `%s` 
                 SET score = (num_views + 3*num_basket_additions + 5*num_purchases) / 9''' % ProductRecord._meta.db_table
        cursor.execute(sql)
        
        logger.info("Updating product table")
        sql = '''UPDATE `%s` product, `%s` analytics
                 SET product.score = analytics.score
                 WHERE product.id = analytics.product_id''' % (Product._meta.db_table, ProductRecord._meta.db_table)
        cursor.execute(sql)
        
        transaction.commit_unless_managed()
        
    def _get_logger(self):
        logger = logging.getLogger('oscar.apps.score_calculation')
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        return logger

        
        
        
            