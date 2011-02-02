from django.utils import unittest
from django.test.client import Client
from django.core.urlresolvers import reverse

        
class CheckoutViewsTest(unittest.TestCase):
    
    def setUp(self):
        self.client = Client()
    
    def test_redirect_returned_when_trying_to_skip_steps(self):
        url = reverse('oscar-checkout-preview')
        response = self.client.get(url)
        self.assertEquals(302, response.status_code)
        
