from django.utils import unittest
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.http import HttpRequest

from oscar.product.models import Item, ItemClass
from oscar.customer.history_helpers import get_recently_viewed_product_ids

class HistoryHelpersTest(unittest.TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Create a dummy product
        ic,_ = ItemClass.objects.get_or_create(name='Dummy class')
        self.dummy_product = Item.objects.create(title='Dummy product', item_class=ic)
        args = {'item_class_slug': self.dummy_product.get_item_class().slug, 
                'item_slug': self.dummy_product.slug,
                'item_id': self.dummy_product.id}
        self.dummy_product_url = reverse('oscar-product-item', kwargs=args)
    
    def test_viewing_product_creates_cookie(self):
        response = self.client.get(self.dummy_product_url)
        self.assertTrue('oscar_recently_viewed_products' in response.cookies)
        
    def test_id_gets_added_to_cookie(self):
        response = self.client.get(self.dummy_product_url)
        request = HttpRequest()
        request.COOKIES['oscar_recently_viewed_products'] = response.cookies['oscar_recently_viewed_products'].value
        self.assertTrue(self.dummy_product.id in get_recently_viewed_product_ids(request))
