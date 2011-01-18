import unittest

from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.product.models import Item, ItemClass
from oscar.stock.models import Partner, StockRecord


class ItemTests(unittest.TestCase):

    def setUp(self):
        self.item_class = ItemClass.objects.create(name='Clothing')
   

class CanonicalItemTests(ItemTests):
    
    def test_canonical_products_must_have_titles(self):
        self.assertRaises(ValidationError, Item.objects.create, item_class=self.item_class)
  
        
class NonCanonicalItemTests(ItemTests):
    
    def setUp(self):
        super(NonCanonicalItemTests, self).setUp()
        self.canonical = Item.objects.create(title="Canonical product", item_class=self.item_class)
    
    def test_non_canonical_products_dont_need_titles(self):
        p = Item.objects.create(parent=self.canonical, item_class=self.item_class)
        
    def test_non_canonical_products_dont_need_a_product_class(self):
        p = Item.objects.create(parent=self.canonical)
        
    def test_non_canonical_products_inherit_canonical_titles(self):
        p = Item.objects.create(parent=self.canonical, item_class=self.item_class)
        self.assertEquals("Canonical product", p.title)
        
    def test_non_canonical_products_inherit_product_class(self):
        p = Item.objects.create(parent=self.canonical)
        self.assertEquals("Clothing", p.item_class.name)