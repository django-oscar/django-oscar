import unittest

from django.test import TestCase

from oscar.core.loading import import_module, AppNotFoundError

class ImportAppTests(unittest.TestCase):

    def test_a_specified_class_is_imported_correctly(self):
        module = import_module('catalogue.models', ['Product'])
        self.assertEqual('oscar.apps.catalogue.models', module.__name__)
        
    def test_unknown_apps_raise_exception(self):
        self.assertRaises(AppNotFoundError, import_module, 'banana', ['skin'])

