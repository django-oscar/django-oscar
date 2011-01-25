import unittest

from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.product.models import Item, ItemClass
from oscar.stock.models import Partner, StockRecord


class ItemTests(unittest.TestCase):

    def setUp(self):
        self.item_class = ItemClass.objects.create(name='Clothing')
   

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