import os
import csv
import sys
from oscar.services import import_module


catalogue_exception = import_module('catalogue_import.exceptions', ['CatalogueImportException'])
product_models = import_module('product.models', ['ItemClass', 'Item', 'AttributeType', 'ItemAttributeValue', 'Option'])
stock_models = import_module('stock.models', ['Partner', 'StockRecord'])

class CatalogueImport(object):
    u"""A catalogue importer object"""
    
    flush = False
    item = []
    
    def handle(self):
        u"""Handles the actual import process"""
        if self.file is None:
            raise catalogue_exception.CatalogueImportException("You need to pass a file argument")
        self.catalogue_import_file = CatalogueImportFile()
        self.catalogue_import_file.file = self.file
        self.test_file()
        if self.flush is True:
            self.flushdb()
        self.csv_content = self.load_csv()
        self.iterate()
    
    def test_file(self):
        u"""Run various tests on the file before import can happen"""
        self.catalogue_import_file.file_exists()
        self.catalogue_import_file.is_file()
        self.catalogue_import_file.file_is_readable()
        
    def flushdb(self):
        u"""Flush out product and stock models"""
        product_models.ItemClass.objects.all().delete()
        product_models.Item.objects.all().delete()
        product_models.AttributeType.objects.all().delete()
        product_models.ItemAttributeValue.objects.all().delete()
        product_models.Option.objects.all().delete()
        stock_models.Partner.objects.all().delete()
        stock_models.StockRecord.objects.all().delete()
        
    def load_csv(self):
        u"""Load the CSV content"""
        csv_reader = CatalogueCsvReader()
        return csv_reader.get_csv_contents(self.file)
    
    def iterate(self):
        u"""Iterate over rows, creating a complete list item"""
        for row in self.csv_content:
            upc, title, description, item_class, partner_name, partner_reference, price_excl_tax, num_in_stock = row
            saved_item_class, _ = product_models.ItemClass.objects.get_or_create(name=item_class)
            try:
                saved_item = product_models.Item.objects.get(upc=upc)
            except product_models.Item.DoesNotExist:
                saved_item = product_models.Item()
            saved_item.upc = upc
            saved_item.title = title
            saved_item.description = description
            saved_item.item_class = saved_item_class
            saved_item.save()
            
            saved_partner, _ = stock_models.Partner.objects.get_or_create(name=partner_name)
            
            try:
                saved_stock, _ = stock_models.StockRecord.objects.get(partner_reference=partner_reference)
            except stock_models.StockRecord.DoesNotExist:
                saved_stock = stock_models.StockRecord()
            
            saved_stock.product = saved_item
            saved_stock.partner = saved_partner
            saved_stock.partner_reference = partner_reference
            saved_stock.price_excl_tax = price_excl_tax
            saved_stock.num_in_stock = num_in_stock
            saved_stock.save()
 
        
class CatalogueImportFile(object):
    u"""A catalogue importer file object"""
    
    def file_exists(self):
        u"""Check whether a file exists"""
        if not os.path.exists(self.file):
            raise catalogue_exception.CatalogueImportException("%s does not exist" % (self.file))
        
    def is_file(self):
        u"""Check whether file is actually a file type"""
        if not os.path.isfile(self.file):
            raise catalogue_exception.CatalogueImportException("%s is not a file" % (self.file))
        
    def file_is_readable(self):
        u"""Check file is readable"""
        try:
            f = open(self.file, 'r')
            f.close()
        except:
            raise catalogue_exception.CatalogueImportException("%s is not readable" % (self.file))
        
        
class CatalogueCsvReader(object):
    u"""A catalogue csv reader"""
    
    def get_csv_contents(self, file):
        u"""Return CSV reader object of file"""
        return csv.reader(open(file,'rb'), delimiter=',', quotechar='"')