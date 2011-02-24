from django.test import TestCase
from oscar.services import import_module

catalogue_exception = import_module('catalogue_import.exceptions', ['CatalogueImportException'])

class FileArgumentTest(TestCase):
    
    def test_sending_no_file_argument(self):
        catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
        importer = catalogue_import.CatalogueImport()
        importer.file = None
        with self.assertRaises(catalogue_exception.CatalogueImportException):
            importer.handle()
 
    def test_sending_directory_as_file(self):
        catalogue_import = import_module('catalogue_import.utils', ['CatalogueImport'])
        importer = catalogue_import.CatalogueImport()
        importer.file = "/tmp"
        with self.assertRaises(catalogue_exception.CatalogueImportException):
            importer.handle()
