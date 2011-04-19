import os
from decimal import Decimal as D
from django.test import TestCase
from oscar.services import import_module

catalogue_exceptions = import_module('catalogue_import.exceptions', ['CatalogueImportException'])
product_models = import_module('product.models', ['ItemClass', 'Item'])
stock_models = import_module('stock.models', ['Partner', 'StockRecord'])


TEST_CSV = os.path.join(os.path.dirname(__file__), 'test.csv')

def setup():
    catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
    importer = catalogue_import.CatalogueImport()
    importer.afile = TEST_CSV
    importer.handle()

class FileArgumentTest(TestCase):

    def test_sending_no_file_argument(self):
        catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
        importer = catalogue_import.CatalogueImport()
        importer.afile = None
        with self.assertRaises(catalogue_exceptions.CatalogueImportException):
            importer.handle()


class FileTypeTest(TestCase):
    
    def test_sending_directory_as_file(self):
        catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
        importer = catalogue_import.CatalogueImport()
        importer.afile = "/tmp"
        with self.assertRaises(catalogue_exceptions.CatalogueImportException):
            importer.handle()


class ImportNonExistentFileTest(TestCase):
    
    def test_importing_file(self):
        catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
        importer = catalogue_import.CatalogueImport()
        importer.afile = "/tmp/catalogue-import.zgvsfsdfsd"
        with self.assertRaises(catalogue_exceptions.CatalogueImportException):
            importer.handle()


class ItemUpcDoesNotExistTest(TestCase):
    
    def test_upc_does_not_exist(self):
        setup()
        with self.assertRaises(product_models.Item.DoesNotExist):
            product_models.Item.objects.get(upc="abcdupc1")


class ItemUpcDoesExistsTest(TestCase):
    
    def test_upc_exists(self):
        setup()
        upc = "abcdupc"
        product = product_models.Item.objects.get(upc=upc)
        self.assertEqual(product.upc, upc)


class ItemClassNameDoesNotExistTest(TestCase):
    
    def test_item_class_name_does_not_exist(self):
        setup()
        with self.assertRaises(product_models.ItemClass.DoesNotExist):
            product_models.ItemClass.objects.get(name="halo")


class ItemClassNameExistsTest(TestCase):
    
    def test_item_class_name_exists(self):
        setup()
        name = "tshirt"
        item_class = product_models.ItemClass.objects.get(name=name)
        self.assertEqual(item_class.name, name)


class PartnerNameDoesNotExistTest(TestCase):
    
    def test_item_class_name_does_not_exist(self):
        setup()
        with self.assertRaises(stock_models.Partner.DoesNotExist):
            stock_models.Partner.objects.get(name="JEFF")

            
class PartnerNameExistsTest(TestCase):
    
    def test_item_class_name_exists(self):
        setup()
        name = "KURA"
        partner = stock_models.Partner.objects.get(name=name)    
        self.assertEqual(partner.name, name)


class PartnerReferenceDoesNotExistTest(TestCase):
    
    def test_partner_reference_does_not_exist(self):
        setup()
        with self.assertRaises(stock_models.StockRecord.DoesNotExist):
            stock_models.StockRecord.objects.get(partner_reference="1234")
        
            
class PartnerRefenceExistsTest(TestCase):
    
    def test_partner_reference_exists(self):
        setup()
        partner_reference = "SKU999"
        stock_record = stock_models.StockRecord.objects.get(partner_reference=partner_reference)
        self.assertEqual(stock_record.partner_reference, partner_reference)
        
class FlushTest(TestCase):
    
    item_class = "hotpants"
    product_upc = "KURA9"
    
    def setup(self):
        item_class, _ = product_models.ItemClass.objects.get_or_create(name=self.item_class)
        
        item = product_models.Item()
        item.upc = self.product_upc
        item.title = "Test item"
        item.description = "Hello there"
        item.item_class = item_class
        item.save()
        
        partner, _ = stock_models.Partner.objects.get_or_create(name="Kura")
        
        stock = stock_models.StockRecord()
        stock.product = item
        stock.partner = partner
        stock.partner_reference = "09090"
        stock.price_excl_tax = D('10.00')
        stock.num_in_stock = 5
        stock.save()
    
    def test_flush(self):
        self.setup()
        catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
        importer = catalogue_import.CatalogueImport()
        importer.afile = TEST_CSV
        importer.flush = True
        importer.handle()
        with self.assertRaises(product_models.Item.DoesNotExist):
            product_models.Item.objects.get(upc=self.product_upc)