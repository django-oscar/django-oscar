import os
import csv
from oscar.services import import_module


catalogue_exception = import_module('catalogue_import.exceptions', ['CatalogueImportException'])
product_models = import_module('product.models', ['ItemClass', 'Item', 'AttributeType', 'ItemAttributeValue', 'Option'])
stock_models = import_module('stock.models', ['Partner', 'StockRecord'])

class CatalogueImport(object):
    u"""A catalogue importer object"""
    
    csv_types = {
                 'simple':['item.upc','item.title','item.description',
                           'itemclass.name','stock.partner','stock.partner_reference',
                           'stock.price_excl_tax','stock.num_in_stock']
                 }
    flush = False
    
    def handle(self):
        u"""Handles the actual import process"""
        if self.file is None:
            raise catalogue_exception.CatalogueImportException("You need to pass a file argument")
        self.catalogue_import_file = CatalogueImportFile()
        self.catalogue_import_file.file = self.file
        self.test_file()
        if self.flush:
            self.flush()
        self.csv_content = self.load_csv()
        self.map_content()
    
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

    def map_content(self):
        u"""Map CSV rows against format"""
        mapper = self.csv_types[self.csv_type]
        map = []
        for line in self.csv_content:
            map.append(zip(mapper, line))
        print map
        
        
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