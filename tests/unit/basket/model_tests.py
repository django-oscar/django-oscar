from django.test import TestCase

from oscar.apps.basket.models import Basket
from oscar.apps.partner import strategy
from oscar.test.factories import (
    BasketFactory, BasketLineAttributeFactory, ProductFactory)


class TestANewBasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()

    def test_has_zero_lines(self):
        self.assertEqual(0, self.basket.num_lines)

    def test_has_zero_items(self):
        self.assertEqual(0, self.basket.num_items)

    def test_doesnt_contain_vouchers(self):
        self.assertFalse(self.basket.contains_a_voucher)

    def test_can_be_edited(self):
        self.assertTrue(self.basket.can_be_edited)

    def test_is_empty(self):
        self.assertTrue(self.basket.is_empty)

    def test_is_not_submitted(self):
        self.assertFalse(self.basket.is_submitted)

    def test_has_no_applied_offers(self):
        self.assertEqual({}, self.basket.applied_offers())


class TestBasketLine(TestCase):

    def test_description(self):
        basket = BasketFactory()
        product = ProductFactory(title="A product")
        basket.add_product(product)

        line = basket.lines.first()
        self.assertEqual(line.description, "A product")

    def test_description_with_attributes(self):
        basket = BasketFactory()
        product = ProductFactory(title="A product")
        basket.add_product(product)

        line = basket.lines.first()
        BasketLineAttributeFactory(
            line=line, value=u'\u2603', option__name='with')
        self.assertEqual(line.description, u"A product (with = '\u2603')")
