from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr

from oscar.apps.shipping import Scales
from oscar.apps.basket.models import Basket
from oscar.test import factories


@attr('shipping')
class TestScales(TestCase):

    def test_weighs_uses_specified_attribute(self):
        scales = Scales(attribute_code='weight')
        p = factories.create_product(attributes={'weight': '1'})
        self.assertEqual(1, scales.weigh_product(p))

    def test_uses_default_weight_when_attribute_is_missing(self):
        scales = Scales(attribute_code='weight', default_weight=0.5)
        p = factories.create_product()
        self.assertEqual(0.5, scales.weigh_product(p))

    def test_raises_exception_when_attribute_is_missing(self):
        scales = Scales(attribute_code='weight')
        p = factories.create_product()
        with self.assertRaises(ValueError):
            scales.weigh_product(p)

    def test_returns_zero_for_empty_basket(self):
        basket = Basket()

        scales = Scales(attribute_code='weight')
        self.assertEqual(0, scales.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket(self):
        basket = factories.create_basket(empty=True)
        products = [
            factories.create_product(attributes={'weight': '1'},
                                     price=D('5.00')),
            factories.create_product(attributes={'weight': '2'},
                                     price=D('5.00'))]
        for product in products:
            basket.add(product)

        scales = Scales(attribute_code='weight')
        self.assertEqual(1 + 2, scales.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket_with_line_quantities(self):
        basket = factories.create_basket(empty=True)
        products = [
            (factories.create_product(attributes={'weight': '1'},
                                      price=D('5.00')), 3),
            (factories.create_product(attributes={'weight': '2'},
                                      price=D('5.00')), 4)]
        for product, quantity in products:
            basket.add(product, quantity=quantity)

        scales = Scales(attribute_code='weight')
        self.assertEqual(1*3 + 2*4, scales.weigh_basket(basket))
