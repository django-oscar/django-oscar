import os
from oscar.services import import_module

catalogue_exception = import_module('catalogue_import.exceptions', ['CatalogueImportException'])

class CatalogueImport(object):
    csv_types = {
                 'simple':('upc','title','description','partner','partner_reference','price_excl_tax','num_in_stock')
                 }
    
    def handle(self):
        if self.file is None:
            raise catalogue_exception.CatalogueImportException("You need to pass a file argument")
        self.check_file_exists()
        self.check_is_file()
        
    def check_file_exists(self):
        if not os.path.exists(self.file):
            raise catalogue_exception.CatalogueImportException("%s does not exist" % (self.file))
        
    def check_is_file(self):
        if not os.path.isfile(self.file):
            raise catalogue_exception.CatalogueImportException("%s is not a file" % (self.file))