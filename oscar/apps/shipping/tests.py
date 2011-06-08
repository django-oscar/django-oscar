from decimal import Decimal as D

from django.utils import unittest
from django.test.client import Client

from oscar.apps.shipping.methods import FreeShipping, FixedPriceShipping
from oscar.apps.shipping.models import OrderAndItemLevelChargeMethod
from oscar.apps.basket.models import Basket
from oscar.test.helpers import create_product
from oscar.test.decorators import dataProvider

class FreeShippingTest(unittest.TestCase):
    
    def test_shipping_is_free(self):
        method = FreeShipping()
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('0.00'), method.basket_charge_incl_tax())
        self.assertEquals(D('0.00'), method.basket_charge_excl_tax())
        
        
class FixedPriceShippingTest(unittest.TestCase):        
    
    def test_fixed_price_shipping_charges_for_empty_basket(self):
        method = FixedPriceShipping(D('10.00'), D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_incl_tax())
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())
        
    def test_fixed_price_shipping_assumes_no_tax(self):
        method = FixedPriceShipping(D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())
        
    shipping_values = lambda: [('1.00',), 
                               ('5.00',), 
                               ('10.00',), 
                               ('12.00',)]    
        
    @dataProvider(shipping_values)    
    def test_different_values(self, value):
        method = FixedPriceShipping(D(value))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D(value), method.basket_charge_excl_tax())
        
        
class OrderAndItemLevelChargeMethodTest(unittest.TestCase):
    
    def setUp(self):
        self.method = OrderAndItemLevelChargeMethod(price_per_order=D('5.00'), price_per_item=D('1.00'))
        self.basket = Basket.objects.create()
        self.method.set_basket(self.basket)
    
    def test_order_level_charge_for_empty_basket(self):
        self.assertEquals(D('5.00'), self.method.basket_charge_incl_tax())
        
    def test_single_item_basket(self):
        p = create_product()
        self.basket.add_product(p)
        self.assertEquals(D('5.00') + D('1.00'), self.method.basket_charge_incl_tax())
        
    def test_multi_item_basket(self):
        p = create_product()
        self.basket.add_product(p, 7)
        self.assertEquals(D('5.00') + 7*D('1.00'), self.method.basket_charge_incl_tax())


class ZeroFreeShippingThresholdTest(unittest.TestCase):
    
    def setUp(self):
        self.method = OrderAndItemLevelChargeMethod(price_per_order=D('10.00'), free_shipping_threshold=D('0.00'))
        self.basket = Basket.objects.create()
        self.method.set_basket(self.basket)
    
    def test_free_shipping_with_empty_basket(self):
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        
    def test_free_shipping_with_nonempty_basket(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())


class NonZeroFreeShippingThresholdTest(unittest.TestCase):
    
    def setUp(self):
        self.method = OrderAndItemLevelChargeMethod(price_per_order=D('10.00'), free_shipping_threshold=D('20.00'))
        self.basket = Basket.objects.create()
        self.method.set_basket(self.basket)
        
    def test_basket_below_threshold(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p)
        self.assertEquals(D('10.00'), self.method.basket_charge_incl_tax())
        
    def test_basket_on_threshold(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p, 4)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        
    def test_basket_above_threshold(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p, 8)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
