from decimal import Decimal

from django.utils import unittest
from django.test.client import Client

from oscar.offer.models import * 
from oscar.basket.models import Basket
from oscar.product.models import Item, ItemClass
from oscar.stock.models import Partner, StockRecord


def create_product(price=None):
    ic,_ = ItemClass.objects.get_or_create(name='Dummy class')
    item = Item.objects.create(title='Dummy product', item_class=ic)
    if price:
        partner,_ = Partner.objects.get_or_create(name="Dummy partner")
        sr = StockRecord.objects.create(product=item, partner=partner, price_excl_tax=price)
    return item


class ConditionTest(unittest.TestCase):
    
    def setUp(self):
        self.range = Range(name="All products", includes_all_products=True)
        self.basket = Basket.objects.create()


class CountConditionTest(ConditionTest):
    
    def setUp(self):
        super(CountConditionTest, self).setUp()
        self.cond = CountCondition(range=self.range, type="Count", value=2)
    
    def test_empty_basket_fails_condition(self):
        self.assertFalse(self.cond.is_satisfied(self.basket))
        
    def test_matching_quantity_basket_passes_condition(self):
        self.basket.add_product(create_product(), 2)
        self.assertTrue(self.cond.is_satisfied(self.basket))
        
    def test_greater_quantity_basket_passes_condition(self):
        self.basket.add_product(create_product(), 3)
        self.assertTrue(self.cond.is_satisfied(self.basket))
        
    
class ValueConditionTest(ConditionTest):
    
    def setUp(self):
        super(ValueConditionTest, self).setUp()
        self.cond = ValueCondition(range=self.range, type="Count", value=Decimal('10.00'))
        self.item = create_product(price=Decimal('5.00'))
    
    def test_empty_basket_fails_condition(self):
        self.assertFalse(self.cond.is_satisfied(self.basket))
        
    def test_less_value_basket_fails_condition(self):
        self.basket.add_product(self.item, 1)
        self.assertFalse(self.cond.is_satisfied(self.basket))    
        
    def test_matching_basket_passes_condition(self):
        self.basket.add_product(self.item, 2)
        self.assertTrue(self.cond.is_satisfied(self.basket))   
        
    def test_greater_than_basket_passes_condition(self):
        self.basket.add_product(self.item, 3)
        self.assertTrue(self.cond.is_satisfied(self.basket)) 
        
   