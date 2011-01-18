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
    
    def test_non_canonical_products_dont_need_titles(self):
        cp = Item.objects.create(title="Canonical product", item_class=self.item_class)
        p = Item.objects.create(parent=cp, item_class=self.item_class)
        self.assertEquals(None, p.title)
        
    def test_non_canonical_products_dont_need_a_product_class(self):
        cp = Item.objects.create(title="Canonical product", item_class=self.item_class)
        p = Item.objects.create(parent=cp)