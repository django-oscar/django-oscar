import os
from decimal import Decimal as D
from django.test import TestCase

from oscar.apps.catalogue_import.utils import Importer
from oscar.apps.catalogue_import.exceptions import CatalogueImportException
from oscar.apps.product.models import ItemClass, Item
from oscar.apps.stock.models import Partner, StockRecord
from oscar.test.helpers import create_product


TEST_CSV = os.path.join(os.path.dirname(__file__), '../fixtures/sample.csv')


class CommandEdgeCasesTest(TestCase):

    def setUp(self):
        self.importer = Importer()

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

    def setUp(self):
        self.importer = Importer()
        self.importer.afile = TEST_CSV
        self.importer.handle()

    def test_item_is_created(self):
        try:
            Item.objects.get(upc="abcdupc")
        except Item.DoesNotExist:
            self.fail() 
            
    def test_item_class_is_created(self):
        try:
            ItemClass.objects.get(name="tshirt")
        except Item.DoesNotExist:
            self.fail() 

    def test_partner_is_created(self):
        try:
            Partner.objects.get(name="KURA")
        except Item.DoesNotExist:
            self.fail() 
    
    def test_stockrecord_is_created(self):
        try:
            StockRecord.objects.get(partner_reference="SKU999")
        except Item.DoesNotExist:
            self.fail()  

        
class ImportWithFlushTest(TestCase):
    
    def setUp(self):
        self.importer = Importer()
        self.importer.afile = TEST_CSV

    def test_items_are_flushed_by_importer(self):
        upc = "KURA9"
        create_product(price=D('10.00'), upc=upc)
        
        self.importer.flush = True
        self.importer.handle()
        
        with self.assertRaises(Item.DoesNotExist):
            Item.objects.get(upc=upc)
   