from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr

from oscar.apps.shipping import methods
from oscar.apps.basket.models import Basket
from oscar.test import factories


@attr('shipping')
class TestFreeShippping(TestCase):

    def setUp(self):
        self.method = methods.Free()

    def test_is_free_for_empty_basket(self):
        basket = Basket()
        self.method.set_basket(basket)
        self.assertEqual(D('0.00'), self.method.charge_incl_tax)
        self.assertEqual(D('0.00'), self.method.charge_excl_tax)

    def test_includes_tax(self):
        basket = Basket()
        self.method.set_basket(basket)
        self.assertTrue(self.method.is_tax_known)

    def test_shipping_is_free_for_nonempty_basket(self):
        basket = factories.create_basket()
        self.method.set_basket(basket)
        self.assertEqual(D('0.00'), self.method.charge_incl_tax)
        self.assertEqual(D('0.00'), self.method.charge_excl_tax)


@attr('shipping')
class TestNoShippingRequired(TestCase):

    def setUp(self):
        self.method = methods.NoShippingRequired()

    def test_is_free_for_empty_basket(self):
        basket = Basket()
        self.method.set_basket(basket)
        self.assertEqual(D('0.00'), self.method.charge_incl_tax)
        self.assertEqual(D('0.00'), self.method.charge_excl_tax)

    def test_has_a_different_code_to_free(self):
        self.assertTrue(methods.NoShippingRequired.code !=
                        methods.Free.code)


@attr('shipping')
class TestFixedPriceShippingWithoutTax(TestCase):

    def setUp(self):
        self.method = methods.FixedPrice(D('10.00'))
        basket = Basket()
        self.method.set_basket(basket)

    def test_has_correct_charge(self):
        self.assertEqual(D('10.00'), self.method.charge_excl_tax)

    def test_does_not_include_tax(self):
        self.assertFalse(self.method.is_tax_known)

    def test_does_not_know_charge_including_tax(self):
        self.assertIsNone(self.method.charge_incl_tax)


@attr('shipping')
class TestFixedPriceShippingWithTax(TestCase):

    def setUp(self):
        self.method = methods.FixedPrice(
            D('10.00'), D('12.00'))
        basket = Basket()
        self.method.set_basket(basket)

    def test_has_correct_charge(self):
        self.assertEqual(D('10.00'), self.method.charge_excl_tax)
        self.assertEqual(D('12.00'), self.method.charge_incl_tax)

    def test_does_include_tax(self):
        self.assertTrue(self.method.is_tax_known)
