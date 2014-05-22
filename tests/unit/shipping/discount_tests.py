from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr
import mock

from oscar.apps.shipping import methods
from oscar.apps.shipping.models import OrderAndItemCharges


@attr('shipping')
class TestStandardMethods(TestCase):

    def setUp(self):
        self.non_discount_methods = [
            methods.Free(),
            methods.FixedPrice(D('10.00'), D('10.00')),
            OrderAndItemCharges(price_per_order=D('5.00'),
                                price_per_item=D('1.00'))]

    def test_have_is_discounted_property(self):
        for method in self.non_discount_methods:
            self.assertFalse(method.is_discounted)


class TestDiscountingMethodsWithoutTax(TestCase):

    def setUp(self):
        self.base_method = methods.FixedPrice(D('10.00'))
        offer = mock.Mock()
        offer.shipping_discount = mock.Mock(
            return_value=D('5.00'))
        self.method = methods.TaxExclusiveOfferDiscount(
            self.base_method, offer)

    def test_delegates_properties_onto_wrapped_method(self):
        self.assertFalse(self.method.is_tax_known)
        self.assertEqual(
            self.method.charge_excl_tax_before_discount, D('10.00'))
        self.assertEqual(self.method.code, self.base_method.code)
        self.assertEqual(self.method.name, self.base_method.name)
        self.assertEqual(self.method.description,
                         self.base_method.description)

    def test_discounts_charge(self):
        self.assertEqual(self.method.charge_excl_tax, D('5.00'))

    def test_correctly_sets_tax(self):
        self.method.tax = D('2.00')
        self.assertTrue(self.method.is_tax_known)
        self.assertEqual(self.method.charge_incl_tax, D('7.00'))
