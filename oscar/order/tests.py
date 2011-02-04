import unittest

from django.test import TestCase
from oscar.basket.models import Basket
from oscar.order.models import *

class ShippingAddressTest(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_titleless_salutation_is_stripped(self):
        a = ShippingAddress.objects.create(last_name='Barrington', line1="75 Smith Road", postcode="N4 8TY")
        self.assertEquals("Barrington", a.get_salutation())
    
        
