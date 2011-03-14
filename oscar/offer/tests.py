from decimal import Decimal
import datetime

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


class OfferTest(unittest.TestCase):
    
    def setUp(self):
        self.range = Range(name="All products", includes_all_products=True)
        self.basket = Basket.objects.create()


class CountConditionTest(OfferTest):
    
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

    def test_consumption(self):
        self.basket.add_product(create_product(), 3)
        self.cond.consume_items(self.basket)
        self.assertEquals(1, self.basket.all_lines()[0].quantity_without_discount)
        
    
class ValueConditionTest(OfferTest):
    
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
        
    def test_consumption(self):
        self.basket.add_product(self.item, 3)
        self.cond.consume_items(self.basket)
        self.assertEquals(1, self.basket.all_lines()[0].quantity_without_discount)

        
class PercentageDiscountBenefitTest(OfferTest):
    
    def setUp(self):
        super(PercentageDiscountBenefitTest, self).setUp()
        self.benefit = PercentageDiscountBenefit(range=self.range, type="PercentageDiscount", value=Decimal('15.00'))
        self.item = create_product(price=Decimal('5.00'))
    
    def test_no_discount_for_empty_basket(self):
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))
        
    def test_discount_for_single_item_basket(self):
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('0.15') * Decimal('5.00'), self.benefit.apply(self.basket))
        
    def test_discount_for_multi_item_basket(self):
        self.basket.add_product(self.item, 3)
        self.assertEquals(Decimal('3') * Decimal('0.15') * Decimal('5.00'), self.benefit.apply(self.basket))
        
    def test_discount_for_multi_item_basket_with_max_affected_items_set(self):
        self.basket.add_product(self.item, 3)
        self.benefit.max_affected_items = 1
        self.assertEquals(Decimal('0.15') * Decimal('5.00'), self.benefit.apply(self.basket))
        
    def test_discount_can_only_be_applied_once(self):
        self.basket.add_product(self.item, 3)
        first_discount = self.benefit.apply(self.basket)
        second_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('0.00'), second_discount)
        
    def test_discount_can_be_applied_several_times_when_max_is_set(self):
        self.basket.add_product(self.item, 3)
        self.benefit.max_affected_items = 1
        for i in range(1, 4):
            self.assertTrue(self.benefit.apply(self.basket) > 0)
        
        
class AbsoluteDiscountBenefitTest(OfferTest):
    
    def setUp(self):
        super(AbsoluteDiscountBenefitTest, self).setUp()
        self.benefit = AbsoluteDiscountBenefit(range=self.range, type="Absolute", value=Decimal('10.00'))
        self.item = create_product(price=Decimal('5.00'))
    
    def test_no_discount_for_empty_basket(self):
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))
        
    def test_discount_for_single_item_basket(self):
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))
        
    def test_discount_for_multi_item_basket(self):
        self.basket.add_product(self.item, 3)
        self.assertEquals(Decimal('10.00'), self.benefit.apply(self.basket))
        
    def test_discount_for_multi_item_basket_with_max_affected_items_set(self):
        self.basket.add_product(self.item, 3)
        self.benefit.max_affected_items = 1
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))
        
    def test_discount_can_only_be_applied_once(self):
        self.basket.add_product(self.item, 3)
        first_discount = self.benefit.apply(self.basket)
        second_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('5.00'), second_discount)
        
    
class ConditionalOfferTest(unittest.TestCase):
   
    def test_is_active(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 01, 10)
        end = datetime.date(2011, 02, 01)
        offer = ConditionalOffer(start_date=start, end_date=end)
        self.assertTrue(offer.is_active(test))
       
    def test_is_inactive(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 03, 10)
        end = datetime.date(2011, 02, 01)
        offer = ConditionalOffer(start_date=start, end_date=end)
        self.assertFalse(offer.is_active(test))
   