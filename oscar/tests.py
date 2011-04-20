import unittest

from django.test import TestCase

from oscar.apps.address.tests import *
from oscar.apps.basket.tests import *
from oscar.apps.order.tests import *
from oscar.apps.product.tests import *
from oscar.apps.stock.tests import *
from oscar.apps.checkout.tests import *
from oscar.apps.payment.tests import *
from oscar.apps.offer.tests import *
from oscar.apps.shipping.tests import *
from oscar.apps.customer.tests import *
from oscar.apps.discount.tests import *
from oscar.apps.promotions.tests import *

from oscar.core.loading import import_module, AppNotFoundError

class ImportAppTests(unittest.TestCase):

    def test_a_specified_class_is_imported_correctly(self):
        module = import_module('product.models', ['Item'])
        self.assertEqual('oscar.apps.product.models', module.__name__)
        
    def test_unknown_apps_raise_exception(self):
        self.assertRaises(AppNotFoundError, import_module, 'banana', ['skin'])
   
    def test_no_classes_specified_raise_exception(self):
        self.assertRaises(ValueError, import_module, 'product.models')

