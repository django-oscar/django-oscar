import unittest

from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.product.models import Item, ItemClass
from oscar.stock.models import Partner, StockRecord

class ItemTest(unittest.TestCase):
    
    def setUp(self):
        self.item_class = ItemClass.objects.create(name='Clothing')
    
    def test_non_canonical_products_dont_need_titles(self):
        cp = Item.objects.create(title="Canonical product", item_class=self.item_class)
        p = Item.objects.create(parent=cp, item_class=self.item_class)
        self.assertEquals('', p.title)
        
    def test_canonical_products_must_have_titles(self):
        self.assertRaises(ValidationError, Item.objects.create, item_class=self.item_class)
        
