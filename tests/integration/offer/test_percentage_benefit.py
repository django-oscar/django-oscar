from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.apps.offer import models
from oscar.test import factories
from oscar.test.basket import add_product, add_products


class TestAPercentageDiscountAppliedWithCountCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition(
            range=product_range, type=models.Condition.COUNT, value=2
        )
        self.benefit = models.PercentageDiscountBenefit(
            range=product_range, type=models.Benefit.PERCENTAGE, value=20
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_with_no_discountable_products(self):
        product = factories.create_product(is_discountable=False)
        add_product(self.basket, D("12.00"), 2, product=product)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2 * D("12.00") * D("0.2"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("12.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(3 * D("12.00") * D("0.2"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAPercentageDiscountWithMaxItemsSetAppliedWithCountCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition(
            range=product_range, type=models.Condition.COUNT, value=2
        )
        self.benefit = models.PercentageDiscountBenefit(
            range=product_range,
            type=models.Benefit.PERCENTAGE,
            value=20,
            max_affected_items=1,
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("12.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("12.00"), 2), (D("20.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("12.00") * D("0.2"), result.discount)
        # Should only consume the condition products
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)


class TestAPercentageDiscountAppliedWithValueCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueCondition.objects.create(
            range=product_range, type=models.Condition.VALUE, value=D("10.00")
        )
        self.benefit = models.PercentageDiscountBenefit.objects.create(
            range=product_range, type=models.Benefit.PERCENTAGE, value=20
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )

        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("5.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_matches_on_boundary(
        self,
    ):
        add_product(self.basket, D("5.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(3 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("4.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(3 * D("4.00") * D("0.2"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAPercentageDiscountWithMaxItemsSetAppliedWithValueCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueCondition.objects.create(
            range=product_range, type=models.Condition.VALUE, value=D("10.00")
        )
        self.benefit = models.PercentageDiscountBenefit.objects.create(
            range=product_range,
            type=models.Benefit.PERCENTAGE,
            value=20,
            max_affected_items=1,
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("5.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_matches_on_boundary(
        self,
    ):
        add_product(self.basket, D("5.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("4.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("4.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)


class TestAPercentageDiscountBenefit(TestCase):
    def test_requires_a_benefit_value(self):
        rng = models.Range.objects.create(name="", includes_all_products=True)
        benefit = models.Benefit(type=models.Benefit.PERCENTAGE, range=rng)
        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_requires_a_range(self):
        benefit = models.Benefit(type=models.Benefit.PERCENTAGE, value=40)
        with self.assertRaises(ValidationError):
            benefit.clean()


class TestPercentageBenefitDiscountAccuracy(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueCondition.objects.create(
            range=product_range, type=models.Condition.COUNT, value=D("1.00")
        )
        self.benefit = models.PercentageDiscountBenefit.objects.create(
            range=product_range, type=models.Benefit.PERCENTAGE, value=D("3.00")
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )
        self.basket = factories.create_basket(empty=True)
        add_product(self.basket, D("2.37"), 6)
        add_product(self.basket, D("3.28"), 1)

    def test_discount_value(self):
        """
        price = 2.37 * 6 + 3.28 = 17.5
        discount = 17.5 * 0.03 = 0.525 = round(0.525) = 0.52
        """
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.52"), result.discount)

    def test_discount_value_round_down(self):
        """
        price = 2.37 * 6 + 3.28 = 17.5
        discount = 17.5 * 0.05 = 0.875 = round(0.875) = 0.87
        """
        self.benefit.value = D("5.00")
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.87"), result.discount)
