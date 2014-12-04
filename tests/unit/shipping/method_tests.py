from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr
import mock

from oscar.apps.shipping import methods
from oscar.apps.basket.models import Basket


@attr('shipping')
class TestFreeShipppingForEmptyBasket(TestCase):

    def setUp(self):
        self.method = methods.Free()
        self.basket = Basket()
        self.charge = self.method.calculate(self.basket)

    def test_is_free(self):
        self.assertEqual(D('0.00'), self.charge.incl_tax)
        self.assertEqual(D('0.00'), self.charge.excl_tax)

    def test_has_tax_known(self):
        self.assertTrue(self.charge.is_tax_known)

    def test_has_same_currency_as_basket(self):
        self.assertEqual(self.basket.currency, self.charge.currency)


@attr('shipping')
class TestFreeShipppingForNonEmptyBasket(TestCase):

    def setUp(self):
        self.method = methods.Free()
        self.basket = mock.Mock()
        self.basket.num_items = 1
        self.charge = self.method.calculate(self.basket)

    def test_is_free(self):
        self.assertEqual(D('0.00'), self.charge.incl_tax)
        self.assertEqual(D('0.00'), self.charge.excl_tax)


@attr('shipping')
class TestNoShippingRequired(TestCase):

    def setUp(self):
        self.method = methods.NoShippingRequired()
        basket = Basket()
        self.charge = self.method.calculate(basket)

    def test_is_free_for_empty_basket(self):
        self.assertEqual(D('0.00'), self.charge.incl_tax)
        self.assertEqual(D('0.00'), self.charge.excl_tax)

    def test_has_a_different_code_to_free(self):
        self.assertTrue(methods.NoShippingRequired.code !=
                        methods.Free.code)


@attr('shipping')
class TestFixedPriceShippingWithoutTax(TestCase):

    def setUp(self):
        self.method = methods.FixedPrice(D('10.00'))
        basket = Basket()
        self.charge = self.method.calculate(basket)

    def test_has_correct_charge(self):
        self.assertEqual(D('10.00'), self.charge.excl_tax)

    def test_does_not_include_tax(self):
        self.assertFalse(self.charge.is_tax_known)


@attr('shipping')
class TestFixedPriceShippingWithTax(TestCase):

    def setUp(self):
        self.method = methods.FixedPrice(
            charge_excl_tax=D('10.00'),
            charge_incl_tax=D('12.00'))
        basket = Basket()
        self.charge = self.method.calculate(basket)

    def test_has_correct_charge(self):
        self.assertEqual(D('10.00'), self.charge.excl_tax)
        self.assertEqual(D('12.00'), self.charge.incl_tax)

    def test_does_include_tax(self):
        self.assertTrue(self.charge.is_tax_known)
