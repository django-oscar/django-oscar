import unittest

from django.test import TestCase

from oscar.core.loading import import_module, AppNotFoundError
from oscar.core.validators import ExtendedURLValidator
from django.core.exceptions import ValidationError

class ImportAppTests(unittest.TestCase):

    def test_a_specified_class_is_imported_correctly(self):
        module = import_module('catalogue.models', ['Product'])
        self.assertEqual('oscar.apps.catalogue.models', module.__name__)
        
    def test_unknown_apps_raise_exception(self):
        self.assertRaises(AppNotFoundError, import_module, 'banana', ['skin'])


class ValidatorTests(unittest.TestCase):
    
    def test_validate_local_url(self):
        v = ExtendedURLValidator(verify_exists=True)
               
        try:
            v('/')
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError unexpectedly!')
            
        try:
            v('/?q=test')  # Query strings shouldn't affect validation
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError unexpectedly!')

        with self.assertRaises(ValidationError):
            v('/invalid/')
        
        with self.assertRaises(ValidationError):
            v('/invalid/?q=test')  # Query strings shouldn't affect validation

        try:
            v('products/')
        except ValidationError:
            self.fail('ExtendedURLValidator raised ValidationError unexpectedly!')
            
        with self.assertRaises(ValidationError):
            v('/products')  # Missing the / is bad          