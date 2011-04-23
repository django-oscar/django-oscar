from decimal import Decimal as D
import datetime

from django.utils import unittest

from oscar.test.helpers import create_product
from oscar.apps.discount.models import DiscountOffer, PERCENTAGE_DISCOUNT, ABSOLUTE_DISCOUNT, FINAL_PRICE 


class PercentageDiscountOfferTest(unittest.TestCase):
    
    def setUp(self):
        self.offer = DiscountOffer(discount_type=PERCENTAGE_DISCOUNT,
                                   discount_value=D('25.00'))
    
    def test_simple_discounted_price(self):
        product = create_product(D('100.00'))
        self.assertEquals(D('75.00'), self.offer._get_discount_price(product))
        
    def test_rounded_discounted_price(self):
        product = create_product(D('99.99'))
        self.assertEquals(D('74.99'), self.offer._get_discount_price(product))

        
class AbsoluteDiscountOfferTest(unittest.TestCase):
    
    def setUp(self):
        self.offer = DiscountOffer(discount_type=ABSOLUTE_DISCOUNT,
                                   discount_value=D('25.00'))
    
    def test_simple_discounted_price(self):
        product = create_product(D('100.00'))
        self.assertEquals(D('75.00'), self.offer._get_discount_price(product))
        
    def test_discount_larger_than_price_sets_price_to_zero(self):
        product = create_product(D('20.00'))
        self.assertEquals(D('0.00'), self.offer._get_discount_price(product))
        
    
class FixedPriceDiscountOfferTest(unittest.TestCase):
    
    def setUp(self):
        self.offer = DiscountOffer(discount_type=FINAL_PRICE,
                                   discount_value=D('25.00'))
    
    def test_simple_discounted_price(self):
        product = create_product(D('100.00'))
        self.assertEquals(D('25.00'), self.offer._get_discount_price(product))
        
    def test_discounted_price_when_original_is_cheaper(self):
        product = create_product(D('20.00'))
        self.assertEquals(D('25.00'), self.offer._get_discount_price(product))    
   