import os
import csv
import sys
from oscar.services import import_module
from oscar.catalogue_import.csv_types import Simple


catalogue_exception = import_module('catalogue_import.exceptions', ['CatalogueImportException'])
product_models = import_module('product.models', ['ItemClass', 'Item', 'AttributeType', 'ItemAttributeValue', 'Option'])
stock_models = import_module('stock.models', ['Partner', 'StockRecord'])

class CatalogueImport(object):
    u"""A catalogue importer object"""
    
    csv_types = {
        'simple': Simple,
    }
    flush = False
    item = []
    
    def handle(self):
        u"""Handles the actual import process"""
        if self.file is None:
            raise catalogue_exception.CatalogueImportException("You need to pass a file argument")
        try:
            self.mapper = self.csv_types[self.csv_type]()
        except:
            raise catalogue_exception.CatalogueImportException("Unable to load CSV mapper: %s" % (csv_type))
        self.catalogue_import_file = CatalogueImportFile()
        self.catalogue_import_file.file = self.file
        self.test_file()
        if self.flush is True:
            self.flush()
        self.csv_content = self.load_csv()
        self.iterate()
    
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
        for row in self.csv_content:
            mapped_row = self.map(row)
            print mapped_row
            print 
            self.item = [] # Create a new list, 'just in-case'
            for item in mapped_row:
                print item
                self.current_item = item # Map to current_item, again 'just in-case'
                self.item.append(item) # Finally append to current mapped item, again 'just in-case'
            print
            print self.item
            print 
            print self.mapper.model_fields
            print
            self.create()
            print 'new row'
            sys.exit()
            
    def create(self):
        model_objects = []
        for model, fields in self.mapper.model_fields:
            print model
            model_object = model()
            model_objects.append({'name': model, 'object': model_object})
            for field in fields:
                for column in self.item:
                    if column[0]['model'] == model and column[0]['field'] == field:
                        print "%s = %s" % (field, column[1])
                        print dir(model_object)
                        vars(model_object)[field] = column[1]
        self.save(model_objects)
        
    def save(self, objects):
        for model in self.mapper.order:
            for save_object in objects:
                if save_object['name'] == model:
                    for fk in self.mapper.fk:
                        if fk['to'] == model:
                            vars(save_object['object'])[fk['as']] = vars()[fk['as']]
                    save_object['object'].save()
                    for fk in self.mapper.fk:
                        if fk['from'] == model:
                            vars()[fk['as']] = save_object['object']

    def map(self, row):
        u"""Map CSV row against format"""
        return zip(self.mapper.fields, row)

        
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