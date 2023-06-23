from decimal import Decimal as D
from unittest import mock

from django.test import TestCase

from oscar.apps.basket.models import Basket
from oscar.apps.shipping import methods


class TestDiscountingMethodsWithoutTax(TestCase):
    def setUp(self):
        self.base_method = methods.FixedPrice(D("10.00"))
        offer = mock.Mock()
        offer.shipping_discount = mock.Mock(return_value=D("2.00"))
        self.method = methods.TaxExclusiveOfferDiscount(self.base_method, offer)

    def test_delegates_properties_onto_wrapped_method(self):
        self.assertEqual(self.method.code, self.base_method.code)
        self.assertEqual(self.method.name, self.base_method.name)
        self.assertEqual(self.method.description, self.base_method.description)

    def test_delegates_is_tax_known(self):
        basket = Basket()
        charge = self.method.calculate(basket)
        self.assertFalse(charge.is_tax_known)

    def test_discounts_charge(self):
        basket = Basket()
        charge = self.method.calculate(basket)
        self.assertEqual(D("8.00"), charge.excl_tax)

    def test_can_have_tax_set_later(self):
        basket = Basket()
        charge = self.method.calculate(basket)
        charge.tax = D("1.00")
        self.assertEqual(D("9.00"), charge.incl_tax)


class TestDiscountingMethodsWithTax(TestCase):
    def setUp(self):
        self.base_method = methods.FixedPrice(D("10.00"), D("12.00"))
        offer = mock.Mock()
        offer.shipping_discount = mock.Mock(return_value=D("5.00"))
        self.method = methods.TaxInclusiveOfferDiscount(self.base_method, offer)

    def test_delegates_properties_onto_wrapped_method(self):
        self.assertEqual(self.method.code, self.base_method.code)
        self.assertEqual(self.method.name, self.base_method.name)
        self.assertEqual(self.method.description, self.base_method.description)

    def test_delegates_is_tax_known(self):
        basket = Basket()
        charge = self.method.calculate(basket)
        self.assertTrue(charge.is_tax_known)

    def test_discounts_charge(self):
        basket = Basket()
        charge = self.method.calculate(basket)
        self.assertEqual(D("7.00"), charge.incl_tax)
