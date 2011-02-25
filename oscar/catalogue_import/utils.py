import os
import csv
from oscar.services import import_module


catalogue_exception = import_module('catalogue_import.exceptions', ['CatalogueImportException'])
product_models = import_module('product.models', ['ItemClass', 'Item', 'AttributeType', 'ItemAttributeValue', 'Option'])
stock_models = import_module('stock.models', ['Partner', 'StockRecord'])

class CatalogueImport(object):
    u"""A catalogue importer object"""
    
    csv_types = {
                 'simple': {'fields': [
                               [product_models.Item, 'upc'],
                               [product_models.Item, 'title'],
                               [product_models.Item, 'description'],
                               [product_models.ItemClass, 'name'],
                               [stock_models.StockRecord, 'partner'],
                               [stock_models.StockRecord, 'partner_reference'],
                               [stock_models.StockRecord, 'price_excl_tax'],
                               [stock_models.StockRecord, 'num_in_stock'],
                           ],
                           'copy_fields': [
                               [[stock_models.StockRecord, 'partner'], [stock_models.Partner, 'name']],
                           ]}
                 }
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
            self.flush()
        self.csv_content = self.load_csv()
        self.iterate()
        for line in self.item:
            print line
    
    def test_file(self):
        u"""Run various tests on the file before import can happen"""
        self.catalogue_import_file.file_exists()
        self.catalogue_import_file.is_file()
        self.catalogue_import_file.file_is_readable()
        
    def flush(self):
        u"""Flush out product and stock models"""
        product_models.ItemClass.objects.all().delete()
        product_models.Item.objects.all().delete()
        product_models.AttributeType.objects.all().delete()
        product_models.ItemAttributeValue.objects.all().delete()
        product_models.Option.objects.all().delete()
        product_models.Partner.objects.all().delete()
        product_models.StockRecord.objects.all().delete()
    def load_csv(self):
        u"""Load the CSV content"""
        csv_reader = CatalogueCsvReader()
        return csv_reader.get_csv_contents(self.file)

    def iterate(self):
        u"""Iterate over rows, creating a complete list item"""
        self.mapper = self.csv_types[self.csv_type]
        for row in self.csv_content:
            mapped_row = self.map(row)
            for item in mapped_row:
                self.current_item = item
                self.item.append(self.current_item)
                self.merge()

    def map(self, row):
        u"""Map CSV row against format"""
        return zip(self.mapper['fields'], row)
        
    def merge(self):
        u"""Locate and merge data from copy field origin to destination"""
        for origin, destination in self.mapper['copy_fields']:
            if origin == self.current_item[0]:
                self.item.append([destination, self.current_item[1]])

        
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