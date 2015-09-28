from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.shipping.scales import Scale
from oscar.apps.basket.models import Basket
from oscar.test import factories


class TestScales(TestCase):

    def test_weighs_uses_specified_attribute(self):
        scale = Scale(attribute_code='weight')
        product = factories.StandaloneProductFactory()
        factories.ProductAttributeValueFactory(product=product, value=1)
        self.assertEqual(1, scale.weigh_product(product))

    def test_uses_default_weight_when_attribute_is_missing(self):
        scale = Scale(attribute_code='weight', default_weight=0.5)
        product = factories.StandaloneProductFactory()
        self.assertEqual(0.5, scale.weigh_product(product))

    def test_raises_exception_when_attribute_is_missing(self):
        scale = Scale(attribute_code='weight')
        product = factories.StandaloneProductFactory()
        with self.assertRaises(ValueError):
            scale.weigh_product(product)

    def test_returns_zero_for_empty_basket(self):
        basket = Basket()

        scale = Scale(attribute_code='weight')
        self.assertEqual(0, scale.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket(self):
        basket = factories.create_basket(empty=True)
        weights = [1, 2]
        for weight in weights:
            attribute_value = factories.ProductAttributeValueFactory(value=weight)
            basket.add(attribute_value.product)

        scale = Scale(attribute_code='weight')
        self.assertEqual(sum(weights), scale.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket_with_line_quantities(self):
        basket = factories.create_basket(empty=True)
        for weight, quantity in [ (1, 3), (2, 4) ]:
            attribute_value = factories.ProductAttributeValueFactory(
                product__stockrecords__price_excl_tax=D('5.00'),
                value=weight)
            basket.add(attribute_value.product, quantity=quantity)

        scale = Scale(attribute_code='weight')
        self.assertEqual(1*3 + 2*4, scale.weigh_basket(basket))
