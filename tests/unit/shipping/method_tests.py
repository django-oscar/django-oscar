from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.shipping import methods
from oscar.apps.basket.models import Basket
from oscar.test import factories


class TestFreeShippping(TestCase):

    def setUp(self):
        self.method = methods.Free()

    def test_is_free_for_empty_basket(self):
        basket = Basket()
        self.method.set_basket(basket)
        self.assertEquals(D('0.00'), self.method.charge_incl_tax)
        self.assertEquals(D('0.00'), self.method.charge_excl_tax)

    def test_shipping_is_free_for_nonempty_basket(self):
        basket = factories.create_basket()
        self.method.set_basket(basket)
        self.assertEquals(D('0.00'), self.method.charge_incl_tax)
        self.assertEquals(D('0.00'), self.method.charge_excl_tax)


class TestNoShippingRequired(TestCase):

    def setUp(self):
        self.method = methods.NoShippingRequired()

    def test_is_free_for_empty_basket(self):
        basket = Basket()
        self.method.set_basket(basket)
        self.assertEquals(D('0.00'), self.method.charge_incl_tax)
        self.assertEquals(D('0.00'), self.method.charge_excl_tax)

    def test_has_a_different_code_to_free(self):
        self.assertTrue(methods.NoShippingRequired.code !=
                        methods.Free.code)


class TestFixedPriceShippingWithoutTax(TestCase):

    def setUp(self):
        self.method = methods.FixedPrice(D('10.00'))
        basket = Basket()
        self.method.set_basket(basket)

    def test_has_correct_charge(self):
        self.assertEquals(D('10.00'), self.method.charge_excl_tax)


class TestFixedPriceShippingWithTax(TestCase):

    def setUp(self):
        self.method = methods.FixedPrice(
            D('12.00'), D('10.00'))
        basket = Basket()
        self.method.set_basket(basket)

    def test_has_correct_charge(self):
        self.assertEquals(D('10.00'), self.method.charge_excl_tax)
        self.assertEquals(D('12.00'), self.method.charge_incl_tax)
