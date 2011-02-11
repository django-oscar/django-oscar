from django.test import TestCase

from oscar.address.models import Country
from oscar.basket.models import Basket
from oscar.order.models import ShippingAddress

class ShippingAddressTest(TestCase):
    
    def setUp(self):
        pass
    
    def test_titleless_salutation_is_stripped(self):
        country = Country.objects.get(iso_3166_1_a2='GB')
        a = ShippingAddress.objects.create(last_name='Barrington', line1="75 Smith Road", postcode="N4 8TY", country=country)
        self.assertEquals("Barrington", a.salutation())
    
        
