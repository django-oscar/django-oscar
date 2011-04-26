from django.utils import unittest
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.http import HttpRequest

from oscar.apps.customer.history_helpers import get_recently_viewed_product_ids
from oscar.test.helpers import create_product

class HistoryHelpersTest(unittest.TestCase):
    
    def setUp(self):
        self.client = Client()
        self.product = create_product()
    
    def test_viewing_product_creates_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertTrue('oscar_recently_viewed_products' in response.cookies)
        
    def test_id_gets_added_to_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        request = HttpRequest()
        request.COOKIES['oscar_recently_viewed_products'] = response.cookies['oscar_recently_viewed_products'].value
        self.assertTrue(self.product.id in get_recently_viewed_product_ids(request))
