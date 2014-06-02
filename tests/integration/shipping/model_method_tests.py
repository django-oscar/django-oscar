from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr

from oscar.apps.shipping.models import OrderAndItemCharges, WeightBased
from oscar.core.compat import get_user_model
from oscar.test import factories


User = get_user_model()


@attr('shipping')
class TestOrderAndItemCharges(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(
            price_per_order=D('5.00'), price_per_item=D('1.00'))

    def test_tax_is_known(self):
        basket = factories.create_basket(empty=True)
        charge = self.method.calculate(basket)
        self.assertTrue(charge.is_tax_known)

    def test_returns_order_level_charge_for_empty_basket(self):
        basket = factories.create_basket(empty=True)
        charge = self.method.calculate(basket)
        self.assertEqual(D('5.00'), charge.incl_tax)

    def test_single_item_basket(self):
        basket = factories.create_basket(empty=False)
        charge = self.method.calculate(basket)
        self.assertEqual(D('5.00') + D('1.00'),
                         charge.incl_tax)

    def test_single_item_basket_that_doesnt_require_shipping(self):
        # Create a product that doesn't require shipping
        record = factories.create_stockrecord()
        product = record.product
        product.product_class.requires_shipping = False
        product.product_class.save()
        basket = factories.create_basket(empty=True)
        basket.add_product(record.product)

        charge = self.method.calculate(basket)

        self.assertEqual(D('5.00'), charge.incl_tax)

    def test_multi_item_basket(self):
        basket = factories.create_basket(empty=True)
        record = factories.create_stockrecord()
        basket.add_product(record.product, 7)

        charge = self.method.calculate(basket)

        self.assertEqual(D('5.00') + 7*D('1.00'), charge.incl_tax)


@attr('shipping')
class ZeroFreeThresholdTest(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(
            price_per_order=D('10.00'), free_shipping_threshold=D('0.00'))
        self.basket = factories.create_basket(empty=True)

    def test_free_shipping_with_empty_basket(self):
        charge = self.method.calculate(self.basket)
        self.assertEqual(D('0.00'), charge.incl_tax)

    def test_free_shipping_with_nonempty_basket(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product)
        charge = self.method.calculate(self.basket)
        self.assertEqual(D('0.00'), charge.incl_tax)


@attr('shipping')
class TestNonZeroFreeThreshold(TestCase):

    def setUp(self):
        self.method = OrderAndItemCharges(
            price_per_order=D('10.00'), free_shipping_threshold=D('20.00'))
        self.basket = factories.create_basket(empty=True)

    def test_basket_below_threshold(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product)

        charge = self.method.calculate(self.basket)

        self.assertEqual(D('10.00'), charge.incl_tax)

    def test_basket_on_threshold(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product, quantity=4)

        charge = self.method.calculate(self.basket)

        self.assertEqual(D('0.00'), charge.incl_tax)

    def test_basket_above_threshold(self):
        record = factories.create_stockrecord(price_excl_tax=D('5.00'))
        self.basket.add_product(record.product, quantity=8)

        charge = self.method.calculate(self.basket)

        self.assertEqual(D('0.00'), charge.incl_tax)


@attr('shipping')
class WeightBasedMethodTests(TestCase):

    def setUp(self):
        self.standard = WeightBased.objects.create(name='Standard')
        self.express = WeightBased.objects.create(name='Express')

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
        charge = self.standard.calculate(basket)
        self.assertEqual(D('0.00'), charge.incl_tax)
        self.assertTrue(charge.is_tax_known)
