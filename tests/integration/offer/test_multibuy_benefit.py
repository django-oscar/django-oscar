from decimal import Decimal as D
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.apps.offer import models
from oscar.apps.offer.utils import Applicator
from oscar.test.basket import add_product, add_products
from oscar.test.factories import (
    BenefitFactory,
    ConditionalOfferFactory,
    ConditionFactory,
    RangeFactory,
    create_basket,
)


class TestAMultibuyDiscountAppliedWithCountCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition.objects.create(
            range=product_range, type=models.Condition.COUNT, value=3
        )
        self.benefit = models.MultibuyDiscountBenefit.objects.create(
            range=product_range, type=models.Benefit.MULTIBUY
        )
        self.offer = mock.Mock()
        self.basket = create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("12.00"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("4.00"), 4), (D("2.00"), 4)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("2.00"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(5, self.basket.num_items_without_discount)

    def test_apply_offer_with_multibuy_benefit_and_count_condition(self):
        rng = RangeFactory(includes_all_products=True)
        condition = ConditionFactory(
            range=rng, type=ConditionFactory._meta.model.COUNT, value=1
        )
        benefit = BenefitFactory(
            range=rng, type=BenefitFactory._meta.model.MULTIBUY, value=1
        )
        offer = ConditionalOfferFactory(condition=condition, benefit=benefit)

        add_product(self.basket, D("100"), 5)

        applicator = Applicator()
        applicator.apply_offers(self.basket, [offer])
        line = self.basket.all_lines()[0]
        assert line.quantity_with_offer_discount(offer) == 1

        self.basket.refresh_from_db()
        assert self.basket.total_discount == D("100")


class TestAMultibuyDiscountAppliedWithAValueCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueCondition.objects.create(
            range=product_range, type=models.Condition.VALUE, value=D("10.00")
        )
        self.benefit = models.MultibuyDiscountBenefit.objects.create(
            range=product_range, type=models.Benefit.MULTIBUY, value=1
        )
        self.offer = mock.Mock()
        self.basket = create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("5.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("5.00"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("4.00"), 2), (D("2.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("2.00"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)


class TestMultibuyValidation(TestCase):
    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition.objects.create(
            range=self.range, type=models.Condition.COUNT, value=3
        )
        self.offer = mock.Mock()
        self.basket = create_basket(empty=True)

    def test_multibuy_range_required(self):
        benefit = models.Benefit(range=None, type=models.Benefit.MULTIBUY, value=1)

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_multibuy_must_not_have_value(self):
        benefit = models.Benefit(
            range=self.range, type=models.Benefit.MULTIBUY, value=1
        )

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_multibuy_must_not_have_max_affected_items(self):
        benefit = models.Benefit(
            range=self.range, type=models.Benefit.MULTIBUY, max_affected_items=2
        )

        with self.assertRaises(ValidationError):
            benefit.clean()
