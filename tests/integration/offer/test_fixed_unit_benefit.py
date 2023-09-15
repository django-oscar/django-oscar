from decimal import Decimal as D
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.apps.offer import models
from oscar.apps.offer.utils import Applicator
from oscar.test import factories
from oscar.test.basket import add_product, add_products


class TestFixedUnitDiscountAppliedWithCountConditionOnDifferentRange(TestCase):
    def setUp(self):
        self.condition_product = factories.ProductFactory()
        condition_range = factories.RangeFactory()
        condition_range.add_product(self.condition_product)
        self.condition = models.CountCondition.objects.create(
            range=condition_range, type=models.Condition.COUNT, value=2
        )

        self.benefit_product = factories.ProductFactory()
        benefit_range = factories.RangeFactory()
        benefit_range.add_product(self.benefit_product)
        self.benefit = models.FixedUnitDiscountBenefit.objects.create(
            range=benefit_range, type=models.Benefit.FIXED_UNIT, value=D("3.00")
        )

        self.offer = models.ConditionalOffer(
            id=1, condition=self.condition, benefit=self.benefit
        )
        self.basket = factories.create_basket(empty=True)

        self.applicator = Applicator()

    def test_succcessful_application_consumes_correctly(self):
        add_product(self.basket, product=self.condition_product, quantity=2)
        add_product(self.basket, product=self.benefit_product, quantity=1)

        self.applicator.apply_offers(self.basket, [self.offer])

        discounts = self.basket.offer_applications.offer_discounts
        self.assertEqual(len(discounts), 1)
        self.assertEqual(discounts[0]["freq"], 1)

    def test_condition_is_consumed_correctly(self):
        # Testing an error case reported on the mailing list
        add_product(self.basket, product=self.condition_product, quantity=3)
        add_product(self.basket, product=self.benefit_product, quantity=2)

        self.applicator.apply_offers(self.basket, [self.offer])

        discounts = self.basket.offer_applications.offer_discounts
        self.assertEqual(len(discounts), 1)
        self.assertEqual(discounts[0]["freq"], 1)


class TestFixedUnitDiscountAppliedWithCountCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition.objects.create(
            range=product_range, type=models.Condition.COUNT, value=2
        )
        self.offer = mock.Mock()
        self.benefit = models.FixedUnitDiscountBenefit.objects.create(
            range=product_range, type=models.Benefit.FIXED_UNIT, value=D("3.00")
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition_with_one_line(self):
        add_product(self.basket, price=D("12.00"), quantity=2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("6.00"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition_with_multiple_lines(
        self,
    ):
        # Use a basket with 2 lines
        add_products(self.basket, [(D("12.00"), 1), (D("12.00"), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)

        self.assertTrue(result.is_successful)
        self.assertFalse(result.is_final)
        self.assertEqual(D("6.00"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition_with_multiple_lines_and_lower_total_value(
        self,
    ):
        # Use a basket with 2 lines
        add_products(self.basket, [(D("1.00"), 1), (D("1.50"), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)

        self.assertTrue(result.is_successful)
        self.assertFalse(result.is_final)
        self.assertEqual(D("2.50"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("12.00"), 2), (D("10.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("12.00"), result.discount)
        self.assertEqual(4, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_with_smaller_prices_than_discount(
        self,
    ):
        add_products(self.basket, [(D("2.00"), 2), (D("4.00"), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("7.00"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_basket_exceeding_condition_smaller_prices_than_discount_higher_prices_first(
        self,
    ):
        add_products(self.basket, [(D("2.00"), 2), (D("4.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("10.00"), result.discount)
        self.assertEqual(4, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestFixedUnitDiscount(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition.objects.create(
            range=product_range, type=models.Condition.COUNT, value=2
        )
        self.benefit = models.FixedUnitDiscountBenefit.objects.create(
            range=product_range, type=models.Benefit.FIXED_UNIT, value=D("4.00")
        )
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_when_discounts_need_rounding(self):
        # Split discount across 3 lines
        for price in [D("2.00"), D("2.00"), D("2.00")]:
            add_product(self.basket, price)
        result = self.benefit.apply(self.basket, self.condition, self.offer)

        self.assertEqual(D("6.00"), result.discount)


class TestFixedUnitDiscountWithMaxItemsSetAppliedWithCountCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition.objects.create(
            range=product_range, type=models.Condition.COUNT, value=2
        )
        self.benefit = models.FixedUnitDiscountBenefit.objects.create(
            range=product_range,
            type=models.Benefit.FIXED_UNIT,
            value=D("3.00"),
            max_affected_items=1,
        )
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("3.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("12.00"), 2), (D("10.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("3.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_with_smaller_prices_than_discount(
        self,
    ):
        add_products(self.basket, [(D("2.00"), 2), (D("1.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("1.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)


class TestFixedUnitDiscountAppliedWithValueCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueCondition.objects.create(
            range=product_range, type=models.Condition.VALUE, value=D("10.00")
        )
        self.benefit = models.FixedUnitDiscountBenefit.objects.create(
            range=product_range, type=models.Benefit.FIXED_UNIT, value=D("3.00")
        )
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D("10.00"), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("3.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D("5.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("6.00"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("4.00"), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("9.00"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(
        self,
    ):
        add_products(self.basket, [(D("5.00"), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("9.00"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestFixedUnitDiscountWithMaxItemsSetAppliedWithValueCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueCondition.objects.create(
            range=product_range, type=models.Condition.VALUE, value=D("10.00")
        )
        self.benefit = models.FixedUnitDiscountBenefit.objects.create(
            range=product_range,
            type=models.Benefit.FIXED_UNIT,
            value=D("3.00"),
            max_affected_items=1,
        )
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D("10.00"), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("3.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D("5.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("3.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("4.00"), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("3.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(
        self,
    ):
        add_products(self.basket, [(D("5.00"), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("3.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition_but_with_lower_prices_than_discount(
        self,
    ):
        add_products(self.basket, [(D("2.00"), 6)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("2.00"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(5, self.basket.num_items_without_discount)


class TestFixedUnitDiscountBenefit(TestCase):
    def test_requires_a_benefit_value(self):
        rng = models.Range.objects.create(name="", includes_all_products=True)
        benefit = models.Benefit(type=models.Benefit.FIXED_UNIT, range=rng)
        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_requires_a_range(self):
        benefit = models.Benefit(type=models.Benefit.FIXED_UNIT, value=10)
        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_non_negative_basket_lines_values(self):
        # absolute product benefit is larger than the line price
        rng = models.Range.objects.create(name="", includes_all_products=True)
        benefit1 = models.Benefit.objects.create(
            type=models.Benefit.FIXED_UNIT, range=rng, value=D("100")
        )
        benefit2 = models.Benefit.objects.create(
            type=models.Benefit.FIXED_UNIT, range=rng, value=D("100")
        )
        condition = models.ValueCondition.objects.create(
            range=rng, type=models.Condition.VALUE, value=D("10")
        )
        models.ConditionalOffer.objects.create(
            name="offer1",
            offer_type=models.ConditionalOffer.SITE,
            benefit=benefit1,
            condition=condition,
            exclusive=False,
        )
        models.ConditionalOffer.objects.create(
            name="offer2",
            offer_type=models.ConditionalOffer.SITE,
            benefit=benefit2,
            condition=condition,
            exclusive=False,
        )

        basket = factories.create_basket(empty=True)
        add_products(basket, [(D("20"), 1)])

        Applicator().apply(basket)
        assert len(basket.offer_applications) == 2
        line = basket.all_lines().first()
        assert line.line_price_excl_tax_incl_discounts == D(0)
        assert line.line_price_incl_tax_incl_discounts == D(0)
        assert basket.total_incl_tax == 0
