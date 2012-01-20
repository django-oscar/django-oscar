from decimal import Decimal as D

from django.utils import unittest
from django.test.client import Client

from oscar.apps.shipping.methods import FreeShipping, FixedPriceShipping, WeightBasedChargesMethod
from oscar.apps.shipping.models import OrderAndItemLevelChargeMethod, WeightBand
from oscar.apps.shipping import Scales
from oscar.apps.basket.models import Basket
from oscar.test.helpers import create_product
from oscar.test.decorators import dataProvider


class FreeShippingTest(unittest.TestCase):

    def setUp(self):
        self.method = FreeShipping()
    
    def test_shipping_is_free_for_empty_basket(self):
        basket = Basket()
        self.method.set_basket(basket)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        self.assertEquals(D('0.00'), self.method.basket_charge_excl_tax())

    def test_shipping_is_free_for_nonempty_basket(self):
        basket = Basket()
        basket.add_product(create_product())
        self.method.set_basket(basket)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())
        self.assertEquals(D('0.00'), self.method.basket_charge_excl_tax())
        
        
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
        
        
class OrderAndItemLevelChargeMethodTests(unittest.TestCase):
    
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


class WeightBasedShippingTests(unittest.TestCase):

    def test_no_bands_leads_to_zero_charges(self):
        method = WeightBasedChargesMethod('dummy')
        basket = Basket.objects.create()
        method.set_basket(basket)

        self.assertEquals(D('0.00'), method.basket_charge_incl_tax())
        self.assertEquals(D('0.00'), method.basket_charge_excl_tax())

    def _test_single_band(self):
        WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        WeightBand.objects.create(method_code='standard', upper_limit=3, charge=D('12.00'))
        method = WeightBasedChargesMethod('standard')

        basket = Basket.objects.create()
        product = get_product
        method.set_basket(basket)


class ScalesTests(unittest.TestCase):

    def test_simple_weight_calculation(self):
        scales = Scales(attribute='weight')
        p = create_product(attributes={'weight': 1})
        self.assertEqual(1, scales.weigh_product(p))

    def test_default_weight_is_used_when_attribute_is_missing(self):
        scales = Scales(attribute='weight', default_weight=0.5)
        p = create_product()
        self.assertEqual(0.5, scales.weigh_product(p))

    def test_exception_is_raised_when_attribute_is_missing(self):
        scales = Scales(attribute='weight')
        p = create_product()
        with self.assertRaises(ValueError):
            scales.weigh_product(p)

    def test_weight_calculation_of_empty_basket(self):
        basket = Basket()

        scales = Scales(attribute='weight')
        self.assertEquals(0, scales.weigh_basket(basket))

    def test_weight_calculation_of_basket(self):
        basket = Basket()
        basket.add_product(create_product(attributes={'weight': 1}))
        basket.add_product(create_product(attributes={'weight': 2}))

        scales = Scales(attribute='weight')
        self.assertEquals(1+2, scales.weigh_basket(basket))


class WeightBandTests(unittest.TestCase):

    def tearDown(self):
        WeightBand.objects.all().delete()

    def test_get_band_for_lower_weight(self):
        band = WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        fetched_band = WeightBand.get_band_for_weight('standard', 0.5)
        self.assertEqual(band.id, fetched_band.id)

    def test_get_band_for_higher_weight(self):
        band = WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        fetched_band = WeightBand.get_band_for_weight('standard', 1.5)
        self.assertIsNone(fetched_band)

    def test_get_band_for_matching_weight(self):
        band = WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        fetched_band = WeightBand.get_band_for_weight('standard', 1)
        self.assertEqual(band.id, fetched_band.id)

    def test_weight_to_is_upper_bound(self):
        band = WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        self.assertEqual(1, band.weight_to)

    def test_weight_from_for_single_band(self):
        band = WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        self.assertEqual(0, band.weight_from)

    def test_weight_from_for_multiple_bands(self):
        WeightBand.objects.create(upper_limit=1, charge=D('4.00'))
        band = WeightBand.objects.create(method_code='standard', upper_limit=2, charge=D('8.00'))
        self.assertEqual(1, band.weight_from)

    def test_weight_from_for_multiple_bands(self):
        WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        band = WeightBand.objects.create(method_code='express', upper_limit=2, charge=D('8.00'))
        self.assertEqual(0, band.weight_from)

    def test_get_band_for_series_of_bands(self):
        WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        WeightBand.objects.create(method_code='standard', upper_limit=2, charge=D('8.00'))
        WeightBand.objects.create(method_code='standard', upper_limit=3, charge=D('12.00'))
        self.assertEqual(D('4.00'), WeightBand.get_band_for_weight('standard', 0.5).charge)
        self.assertEqual(D('8.00'), WeightBand.get_band_for_weight('standard', 1.5).charge)
        self.assertEqual(D('12.00'), WeightBand.get_band_for_weight('standard', 2.5).charge)

    def test_get_band_for_series_of_bands_from_different_methods(self):
        WeightBand.objects.create(method_code='standard', upper_limit=1, charge=D('4.00'))
        WeightBand.objects.create(method_code='express', upper_limit=2, charge=D('8.00'))
        WeightBand.objects.create(method_code='standard', upper_limit=3, charge=D('12.00'))
        self.assertEqual(D('12.00'), WeightBand.get_band_for_weight('standard', 2.5).charge)
