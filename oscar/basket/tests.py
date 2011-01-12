import unittest

from django.test import TestCase
from oscar.basket.models import * 
from oscar.product.models import Item, ItemClass

class BasketTest(unittest.TestCase):
    
    def setUp(self):
        self.basket = Basket.objects.create()
        
        # Create a dummy product
        ic = ItemClass.objects.create(name='Dummy class')
        self.dummy_product = Item.objects.create(title='Dummy product', item_class=ic)
    
    def test_empty_baskets_have_zero_lines(self):
        self.assertTrue(Basket().get_num_lines() == 0)
        
    def test_new_baskets_are_empty(self):
        self.assertTrue(Basket().is_empty())
        
    def test_basket_have_with_one_line(self):
        line = Line.objects.create(basket=self.basket, product=self.dummy_product)
        self.assertTrue(self.basket.get_num_lines() == 1)
        
    def test_add_product_creates_line(self):
        self.basket.add_product(self.dummy_product)
        self.assertTrue(self.basket.get_num_lines() == 1)
        
    def test_adding_multiproduct_line_returns_correct_number_of_items(self):
        self.basket.add_product(self.dummy_product, 10)
        self.assertEqual(self.basket.get_num_items(), 10)
        
if __name__ == '__main__':
    from django.test.utils import setup_test_environment
    setup_test_environment()
    unittest.main()