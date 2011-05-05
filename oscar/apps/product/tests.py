import unittest

from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from oscar.apps.product.models import Item, ItemClass
from oscar.apps.partner.models import Partner, StockRecord


class ItemTests(unittest.TestCase):

    def setUp(self):
        self.item_class,_ = ItemClass.objects.get_or_create(name='Clothing')
   

class TopLevelItemTests(ItemTests):
    
    def test_top_level_products_must_have_titles(self):
        self.assertRaises(ValidationError, Item.objects.create, item_class=self.item_class)
        
        
class VariantItemTests(ItemTests):
    
    def setUp(self):
        super(VariantItemTests, self).setUp()
        self.parent = Item.objects.create(title="Parent product", item_class=self.item_class)
    
    def test_variant_products_dont_need_titles(self):
        p = Item.objects.create(parent=self.parent, item_class=self.item_class)
        
    def test_variant_products_dont_need_a_product_class(self):
        p = Item.objects.create(parent=self.parent)
        
    def test_variant_products_inherit_parent_titles(self):
        p = Item.objects.create(parent=self.parent, item_class=self.item_class)
        self.assertEquals("Parent product", p.get_title())
        
    def test_variant_products_inherit_product_class(self):
        p = Item.objects.create(parent=self.parent)
        self.assertEquals("Clothing", p.get_item_class().name)
        

class SingleProductViewTest(TestCase):
    fixtures = ['sample-products']
    
    def setUp(self):
        self.client = Client()
        
    def test_canonical_urls_are_enforced(self):
        p = Item.objects.get(id=1)
        args = {'item_class_slug': p.get_item_class().slug, 
                'item_slug': 'wrong-slug',
                'item_id': p.id}
        wrong_url = reverse('oscar-product-item', kwargs=args)
        response = self.client.get(wrong_url)
        self.assertEquals(301, response.status_code)