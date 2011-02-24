import unittest

from django.test import TestCase

from oscar.address.tests import *
from oscar.basket.tests import *
from oscar.order.tests import *
from oscar.product.tests import *
from oscar.stock.tests import *
from oscar.checkout.tests import *
from oscar.catalogue_import.tests import *

from oscar.services import import_module, AppNotFoundError


class ImportAppTests(unittest.TestCase):

    def test_a_specified_class_is_imported_correctly(self):
        module = import_module('product.models', ['Item'])
        self.assertEqual('oscar.product.models', module.__name__)
        
    def test_unknown_apps_raise_exception(self):
        self.assertRaises(AppNotFoundError, import_module, 'banana', ['skin'])
   
    def test_no_classes_specified_raise_exception(self):
        self.assertRaises(ValueError, import_module, 'product.models')

