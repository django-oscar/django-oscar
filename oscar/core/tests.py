from django.test import TestCase

from oscar.core.loading import import_module, AppNotFoundError, \
        get_classes
from oscar.core.validators import ExtendedURLValidator
from django.core.exceptions import ValidationError


class ImportAppTests(TestCase):

    def test_a_specified_class_is_imported_correctly(self):
        module = import_module('analytics.models', ['ProductRecord'])
        self.assertEqual('oscar.apps.analytics.models', module.__name__)
        
    def test_unknown_apps_raise_exception(self):
        self.assertRaises(AppNotFoundError, import_module, 'banana', ['skin'])


class ClassLoadingTests(TestCase):

    def test_loading_oscar_classes(self):
        Product, Category = get_classes('catalogue.models', ('Product', 'Category'))
        self.assertEqual('oscar.apps.catalogue.models', Product.__module__)
        self.assertEqual('oscar.apps.catalogue.models', Category.__module__)

    def test_bad_appname_raises_exception(self):
        with self.assertRaises(ValueError):
            Product, Category = get_classes('fridge.models', ('Product', 'Category'))

    def _test_loading_local_project_class(self):
        (Importer,) = get_classes('catalogue.utils', ('Importer',))
        self.assertEqual('tests.catalogue.utils', Importer.__module__)


class ValidatorTests(TestCase):
    
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
