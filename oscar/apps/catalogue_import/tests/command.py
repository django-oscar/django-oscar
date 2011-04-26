import os
from decimal import Decimal as D
from django.test import TestCase
import logging

from oscar.apps.catalogue_import.utils import Importer
from oscar.apps.catalogue_import.exceptions import CatalogueImportException
from oscar.apps.product.models import ItemClass, Item
from oscar.apps.stock.models import Partner, StockRecord
from oscar.test.helpers import create_product

TEST_BOOKS_CSV = os.path.join(os.path.dirname(__file__), '../fixtures/books-small.csv')
TEST_BOOKS_SEMICOLON_CSV = os.path.join(os.path.dirname(__file__), '../fixtures/books-small-semicolon.csv')

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logger = logging.getLogger("Null")
logger.addHandler(NullHandler())


class CommandEdgeCasesTest(TestCase):

    def setUp(self):
        self.importer = Importer(logger)

    def test_sending_no_file_argument_raises_exception(self):
        self.importer.afile = None
        with self.assertRaises(CatalogueImportException):
            self.importer.handle()

    def test_sending_directory_as_file_raises_exception(self):
        self.importer.afile = "/tmp"
        with self.assertRaises(CatalogueImportException):
            self.importer.handle()

    def test_importing_nonexistant_file_raises_exception(self):
        self.importer.afile = "/tmp/catalogue-import.zgvsfsdfsd"
        with self.assertRaises(CatalogueImportException):
            self.importer.handle()


class ImportSmokeTest(TestCase):
    
    # First row is:
    # "9780115531446","Prepare for Your Practical Driving Test",NULL,"Book","Gardners","9780115531446","10.32","6"
    #
    # Second row is (has no stock data):
    # "9780955337819","Better Photography",NULL,"Book"
    
    
    def setUp(self):
        self.importer = Importer(logger)
        self.importer.handle(TEST_BOOKS_CSV)
        self.item = Item.objects.get(upc='9780115531446')
        
    def test_all_rows_are_imported(self):
        self.assertEquals(10, Item.objects.all().count())
        
    def test_class_is_created(self):
        try:
            ItemClass.objects.get(name="Book")
        except Item.DoesNotExist:
            self.fail()  
    
    def test_item_is_created(self):
        try:
            Item.objects.get(upc="9780115531446")
        except Item.DoesNotExist:
            self.fail()         
    
    def test_title_is_imported(self):
        self.assertEquals("Prepare for Your Practical Driving Test", self.item.title)
        
    def test_partner_is_created(self):
        try:
            Partner.objects.get(name="Gardners")
        except Item.DoesNotExist:
            self.fail() 
    
    def test_stockrecord_is_created(self):
        try:
            StockRecord.objects.get(partner_reference="9780115531446")
        except Item.DoesNotExist:
            self.fail()      
        
    def test_null_fields_are_skipped(self):
        self.assertEquals("", self.item.description)
        
    def test_price_is_imported(self):
        self.assertEquals(D('10.32'), self.item.stockrecord.price_excl_tax)
        
    def test_num_in_stock_is_imported(self):
        self.assertEquals(6, self.item.stockrecord.num_in_stock)
        
        
class ImportSemicolonDelimitedFileTest(TestCase):
    
    def setUp(self):
        self.importer = Importer(logger, delimiter=";")
        
    def test_import(self):
        self.importer.handle(TEST_BOOKS_SEMICOLON_CSV)
    
    
class ImportWithFlushTest(TestCase):
    
    def setUp(self):
        self.importer = Importer(logger, flush=True)

    def test_items_are_flushed_by_importer(self):
        upc = "0000000000000"
        create_product(price=D('10.00'), upc=upc)
        
        self.importer.handle(TEST_BOOKS_CSV)
        
        with self.assertRaises(Item.DoesNotExist):
            Item.objects.get(upc=upc)
   