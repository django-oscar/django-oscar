from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.basket.models import Basket
from oscar.apps.shipping.scales import Scale
from oscar.test import factories


class TestScales(TestCase):
    def test_weighs_uses_specified_attribute(self):
        scale = Scale(attribute_code="weight")
        p = factories.create_product(attributes={"weight": "1"})
        self.assertEqual(1, scale.weigh_product(p))

    def test_uses_default_weight_when_attribute_is_missing(self):
        scale = Scale(attribute_code="weight", default_weight=0.5)
        p = factories.create_product()
        self.assertEqual(0.5, scale.weigh_product(p))

    def test_raises_exception_when_attribute_is_missing(self):
        scale = Scale(attribute_code="weight")
        p = factories.create_product()
        with self.assertRaises(ValueError):
            scale.weigh_product(p)

    def test_returns_zero_for_empty_basket(self):
        basket = Basket()

        scale = Scale(attribute_code="weight")
        self.assertEqual(0, scale.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket(self):
        basket = factories.create_basket(empty=True)
        products = [
            factories.create_product(attributes={"weight": "1"}, price=D("5.00")),
            factories.create_product(attributes={"weight": "2"}, price=D("5.00")),
        ]
        for product in products:
            basket.add(product)

        scale = Scale(attribute_code="weight")
        self.assertEqual(1 + 2, scale.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket_with_line_quantities(self):
        basket = factories.create_basket(empty=True)
        products = [
            (factories.create_product(attributes={"weight": "1"}, price=D("5.00")), 3),
            (factories.create_product(attributes={"weight": "2"}, price=D("5.00")), 4),
        ]
        for product, quantity in products:
            basket.add(product, quantity=quantity)

        scale = Scale(attribute_code="weight")
        self.assertEqual(1 * 3 + 2 * 4, scale.weigh_basket(basket))

    def test_decimals(self):
        basket = factories.create_basket(empty=True)
        product = factories.create_product(
            attributes={"weight": "0.3"}, price=D("5.00")
        )
        basket.add(product)

        scale = Scale(attribute_code="weight")
        self.assertEqual(D("0.3"), scale.weigh_basket(basket))

        basket.add(product)
        self.assertEqual(D("0.6"), scale.weigh_basket(basket))

        basket.add(product)
        self.assertEqual(D("0.9"), scale.weigh_basket(basket))
