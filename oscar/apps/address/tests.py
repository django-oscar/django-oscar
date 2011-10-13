# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.test import TestCase

from oscar.apps.address.models import Country, UserAddress
from oscar.apps.order.models import ShippingAddress


class UserAddressTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create(username='dummy_user')
        self.country = Country.objects.get(iso_3166_1_a2='GB')
    
    def tearDown(self):
        self.user.delete()
    
    def test_titleless_salutation_is_stripped(self):
        a = UserAddress.objects.create(last_name='Barrington', line1="75 Smith Road", postcode="N4 8TY", 
                                       country=self.country, user=self.user)
        self.assertEquals("Barrington", a.salutation())
    
    def test_postcodes_are_saved_in_uppercase(self):
        a = UserAddress.objects.create(last_name='Barrington', line1="75 Smith Road", postcode="n4 8ty", 
                                       country=self.country, user=self.user)
        self.assertEquals("N4 8TY", a.postcode)   
        
    def test_fields_are_stripped_when_saved(self):
        a = UserAddress.objects.create(last_name='Barrington', line1="  75 Smith Road  ", postcode="  n4 8ty", 
                                       country=self.country, user=self.user)
        self.assertEquals("N4 8TY", a.postcode)      
        
    def test_active_address_fields_skips_whitespace_only_fields(self):
        a = UserAddress(first_name="   ", last_name='Barrington', line1="  75 Smith Road  ", postcode="  n4 8ty", 
                        country=self.country, user=self.user)
        active_fields = a.active_address_fields()
        self.assertEquals("Barrington", active_fields[0])   
        
    def test_summary_is_property(self):
        a = UserAddress(first_name=" Terry  ", last_name='Barrington', line1="  75 Smith Road  ", postcode="  n4 8ty", 
                        country=self.country, user=self.user)
        self.assertEquals("Terry Barrington, 75 Smith Road, N4 8TY, UNITED KINGDOM", a.summary)
        
    def test_populate_shipping_address_doesnt_set_id(self):
        a = UserAddress(first_name=" Terry  ", last_name='Barrington', line1="  75 Smith Road  ", postcode="  n4 8ty", 
                        country=self.country, user=self.user)
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertIsNone(sa.id)
        
    def test_populated_shipping_address_has_same_summary_user_address(self):
        a = UserAddress(first_name=" Terry  ", last_name='Barrington', line1="  75 Smith Road  ", postcode="  n4 8ty", 
                        country=self.country, user=self.user)
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertEquals(sa.summary, a.summary)
        
    def test_addresses_with_same_fields_ignoring_whitespace_have_same_hash(self):
        a1 = UserAddress(first_name=" Terry  ", last_name='Barrington', line1="  75 Smith Road  ", postcode="  n4 8ty", 
                         country=self.country, user=self.user)
        a2 = UserAddress(first_name=" Terry", last_name='   Barrington', line1="  75 Smith Road  ", postcode="N4 8ty", 
                         country=self.country, user=self.user)
        self.assertEquals(a1.generate_hash(), a2.generate_hash())
        
    def test_hashing_with_utf8(self):
        a = UserAddress(first_name=u"\u0141ukasz Smith", last_name=u'Smith', line1=u"75 Smith Road", postcode=u"n4 8ty", 
                        country=self.country, user=self.user)
        hash = a.active_address_fields()
        
    def test_city_is_alias_of_line4(self):
        a = UserAddress.objects.create(last_name='Barrington', line1="75 Smith Road", line4="London", postcode="n4 8ty", 
                                       country=self.country, user=self.user)
        self.assertEqual('London', a.city)
           
