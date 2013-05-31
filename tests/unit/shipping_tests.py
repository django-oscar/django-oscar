from decimal import Decimal as D

from django.test import TestCase
from django.contrib.auth.models import User

from oscar.apps.shipping.methods import Free, FixedPrice
from oscar.apps.shipping.models import OrderAndItemCharges, WeightBased
from oscar.apps.shipping.repository import Repository
from oscar.apps.shipping import Scales
from oscar.apps.basket.models import Basket
from oscar_testsupport.factories import create_product


class FreeTest(TestCase):

    def setUp(self):
        self.method = Free()

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


class FixedPriceTest(TestCase):

    def test_fixed_price_shipping_charges_for_empty_basket(self):
        method = FixedPrice(D('10.00'), D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_incl_tax())
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())

    def test_fixed_price_shipping_assumes_no_tax(self):
        method = FixedPrice(D('10.00'))
        basket = Basket()
        method.set_basket(basket)
        self.assertEquals(D('10.00'), method.basket_charge_excl_tax())

    def test_different_values(self):
        shipping_values = ['1.00', '5.00', '10.00', '12.00']
        for value in shipping_values:
            basket = Basket()
            method = FixedPrice(D(value))
            method.set_basket(basket)
            self.assertEquals(D(value), method.basket_charge_excl_tax())


class OrderAndItemChargesTests(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(price_per_order=D('5.00'), price_per_item=D('1.00'))
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


class ZeroFreeThresholdTest(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(price_per_order=D('10.00'), free_shipping_threshold=D('0.00'))
        self.basket = Basket.objects.create()
        self.method.set_basket(self.basket)

    def test_free_shipping_with_empty_basket(self):
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())

    def test_free_shipping_with_nonempty_basket(self):
        p = create_product(D('5.00'))
        self.basket.add_product(p)
        self.assertEquals(D('0.00'), self.method.basket_charge_incl_tax())


class NonZeroFreeThresholdTest(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(price_per_order=D('10.00'), free_shipping_threshold=D('20.00'))
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


class ScalesTests(TestCase):

    def test_simple_weight_calculation(self):
        scales = Scales(attribute_code='weight')
        p = create_product(attributes={'weight': 1})
        self.assertEqual(1, scales.weigh_product(p))

    def test_default_weight_is_used_when_attribute_is_missing(self):
        scales = Scales(attribute_code='weight', default_weight=0.5)
        p = create_product()
        self.assertEqual(0.5, scales.weigh_product(p))

    def test_exception_is_raised_when_attribute_is_missing(self):
        scales = Scales(attribute_code='weight')
        p = create_product()
        with self.assertRaises(ValueError):
            scales.weigh_product(p)

    def test_weight_calculation_of_empty_basket(self):
        basket = Basket()

        scales = Scales(attribute_code='weight')
        self.assertEquals(0, scales.weigh_basket(basket))

    def test_weight_calculation_of_basket(self):
        basket = Basket()
        basket.add_product(create_product(attributes={'weight': 1}))
        basket.add_product(create_product(attributes={'weight': 2}))

        scales = Scales(attribute_code='weight')
        self.assertEquals(1+2, scales.weigh_basket(basket))

    def test_weight_calculation_of_basket_with_line_quantity(self):
        basket = Basket()
        basket.add_product(create_product(attributes={'weight': 1}), quantity=3)
        basket.add_product(create_product(attributes={'weight': 2}), quantity=4)

        scales = Scales(attribute_code='weight')
        self.assertEquals(1*3+2*4, scales.weigh_basket(basket))


class WeightBasedMethodTests(TestCase):

    def setUp(self):
        self.standard = WeightBased.objects.create(name='Standard')
        self.express = WeightBased.objects.create(name='Express')

    def tearDown(self):
        self.standard.delete()
        self.express.delete()

    def test_get_band_for_lower_weight(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        fetched_band = self.standard.get_band_for_weight(0.5)
        self.assertEqual(band.id, fetched_band.id)

    def test_get_band_for_higher_weight(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        fetched_band = self.standard.get_band_for_weight(1.5)
        self.assertIsNone(fetched_band)

    def test_get_band_for_matching_weight(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        fetched_band = self.standard.get_band_for_weight(1)
        self.assertEqual(band.id, fetched_band.id)

    def test_weight_to_is_upper_bound(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.assertEqual(1, band.weight_to)

    def test_weight_from_for_single_band(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.assertEqual(0, band.weight_from)

    def test_weight_from_for_multiple_bands(self):
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        band = self.standard.objects.create(upper_limit=2, charge=D('8.00'))
        self.assertEqual(1, band.weight_from)

    def test_weight_from_for_multiple_bands(self):
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        band = self.express.bands.create(upper_limit=2, charge=D('8.00'))
        self.assertEqual(0, band.weight_from)

    def test_get_band_for_series_of_bands(self):
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.standard.bands.create(upper_limit=2, charge=D('8.00'))
        self.standard.bands.create(upper_limit=3, charge=D('12.00'))
        self.assertEqual(D('4.00'), self.standard.get_band_for_weight(0.5).charge)
        self.assertEqual(D('8.00'), self.standard.get_band_for_weight(1.5).charge)
        self.assertEqual(D('12.00'), self.standard.get_band_for_weight(2.5).charge)

    def test_get_band_for_series_of_bands_from_different_methods(self):
        self.express.bands.create(upper_limit=2, charge=D('8.00'))
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        self.standard.bands.create(upper_limit=3, charge=D('12.00'))
        self.assertEqual(D('12.00'), self.standard.get_band_for_weight(2.5).charge)

    def test_for_smoke_with_basket_charge(self):
        basket = Basket()
        self.standard.set_basket(basket)
        charge = self.standard.basket_charge_incl_tax()
        self.assertEqual(D('0.00'), charge)


class OfferDiscountTest(TestCase):
    """
    Should test a discounted shipping method against a non-discounted one.
    So far only checks if the is_discounted field is present on all
    methods
    """

    def setUp(self):
        self.non_discount_methods = [
            Free(),
            FixedPrice(D('10.00'), D('10.00')),
            OrderAndItemCharges(price_per_order=D('5.00'), price_per_item=D('1.00'))]
        self.discount_methods = []

    def test_is_discounted_present_and_reasonable(self):
        for method in self.non_discount_methods + self.discount_methods:
            self.assertTrue(hasattr(method, 'is_discounted'))
        for method in self.non_discount_methods:
            self.assertFalse(method.is_discounted)
        for method in self.discount_methods:
            self.assertTrue(method.is_discounted)


class RepositoryTests(TestCase):

    def setUp(self):
        self.repo = Repository()

    def test_default_method_is_free(self):
        user, basket = User(), Basket()
        methods = self.repo.get_shipping_methods(user, basket)
        self.assertEqual(1, len(methods))
        self.assertTrue(isinstance(methods[0], Free))

