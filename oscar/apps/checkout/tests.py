from decimal import Decimal as D

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from oscar.test.helpers import create_product

        
class CheckoutViewsTest(TestCase):
    
    fixtures = ['example-shipping-charges.json']
    
    def setUp(self):
        self.client = Client()
        super(CheckoutViewsTest, self).setUp()
    
    def _test_anonymous_checkout(self):
        
        # Add a product to the basket
        p = create_product(price=D('10.00'))
        response = self.client.post(reverse('basket:add'), {'action': 'add', 
                                                              'product_id': str(p.id),
                                                              'quantity': 1})
        self.assertEqual(302, response.status_code)
        
        # Submit shipping address
        response = self.client.post(reverse('oscar-checkout-shipping-address'), 
                                    {'last_name': 'Smith',
                                     'line1': '1 Portland Street',
                                     'postcode': 'N12 9ET',
                                     'country': 'GB'})
        self.assertEqual(302, response.status_code)
        
        # Choose shipping method
        response = self.client.post(reverse('oscar-checkout-shipping-method'),
                                    {'method_code': 'royal-mail-first-class'})
        self.assertEqual(302, response.status_code)
        
        # Shipping method
        response = self.client.get(reverse('oscar-checkout-payment-method'))
        self.assertEqual(302, response.status_code)
        
        # View preview
        response = self.client.get(reverse('oscar-checkout-preview'))
        self.assertEqual(302, response.status_code)
        
        # Submit
        response = self.client.post(reverse('oscar-checkout-payment-details'), {})
        self.assertEqual(302, response.status_code)
        
        
        
        
        
        
