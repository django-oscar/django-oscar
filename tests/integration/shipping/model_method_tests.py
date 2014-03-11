from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr

from oscar.apps.shipping.models import OrderAndItemCharges, WeightBased
from oscar.core.compat import get_user_model
from oscar.test import factories


User = get_user_model()


@attr('shipping')
class OrderAndItemChargesTests(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(
            price_per_order=D('5.00'), price_per_item=D('1.00'))
        self.basket = factories.create_basket(empty=True)
        self.method.set_basket(self.basket)

    def test_tax_is_known(self):
        self.assertTrue(self.method.is_tax_known)

    def test_order_level_charge_for_empty_basket(self):
        self.assertEqual(D('5.00'), self.method.charge_incl_tax)

    def test_single_item_basket(self):
        record = factories.create_stockrecord()
        self.basket.add_product(record.product)
        self.assertEqual(D('5.00') + D('1.00'),
                          self.method.charge_incl_tax)

    def test_single_item_basket_that_doesnt_require_shipping(self):
        # Create a product that doesn't require shipping
        record = factories.create_stockrecord()
        product = record.product
        product.product_class.requires_shipping = False
        product.product_class.save()

        self.basket.add_product(record.product)
        self.assertEquals(D('5.00'), self.method.charge_incl_tax)

    def test_multi_item_basket(self):
        record = factories.create_stockrecord()
        self.basket.add_product(record.product, 7)
        self.assertEqual(D('5.00') + 7*D('1.00'), self.method.charge_incl_tax)


@attr('shipping')
class ZeroFreeThresholdTest(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(price_per_order=D('10.00'), free_shipping_threshold=D('0.00'))
        self.basket = factories.create_basket(empty=True)
        self.method.set_basket(self.basket)

    def test_free_shipping_with_empty_basket(self):
        self.assertEqual(D('0.00'), self.method.charge_incl_tax)

    def test_free_shipping_with_nonempty_basket(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product)
        self.assertEqual(D('0.00'), self.method.charge_incl_tax)


@attr('shipping')
class NonZeroFreeThresholdTest(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(
            price_per_order=D('10.00'), free_shipping_threshold=D('20.00'))
        self.basket = factories.create_basket(empty=True)
        self.method.set_basket(self.basket)

    def test_basket_below_threshold(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product)
        self.assertEqual(D('10.00'), self.method.charge_incl_tax)

    def test_basket_on_threshold(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product, quantity=4)
        self.assertEqual(D('0.00'), self.method.charge_incl_tax)

    def test_basket_above_threshold(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product, quantity=8)
        self.assertEqual(D('0.00'), self.method.charge_incl_tax)


@attr('shipping')
class WeightBasedMethodTests(TestCase):

    def setUp(self):
        self.standard = WeightBased.objects.create(name='Standard')
        self.express = WeightBased.objects.create(name='Express')

    def tearDown(self):
        self.standard.delete()
        self.express.delete()

    def test_tax_is_known(self):
        self.assertTrue(self.standard.is_tax_known)
        self.assertTrue(self.express.is_tax_known)

    def test_get_band_for_lower_weight(self):
        band = self.standard.bands.create(upper_limit=1, charge=D('4.00'))
        fetched_band = self.standard.get_band_for_weight(0.5)
        self.assertEqual(band.id, fetched_band.id)

    def test_get_band_for_higher_weight(self):
        self.standard.bands.create(upper_limit=1, charge=D('4.00'))
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
        basket = factories.create_basket(empty=True)
        self.standard.set_basket(basket)
        charge = self.standard.charge_incl_tax
        self.assertEqual(D('0.00'), charge)


