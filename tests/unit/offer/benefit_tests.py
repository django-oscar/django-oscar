from decimal import Decimal

from django.conf import settings

from oscar.apps.basket.models import Basket
from oscar.apps.offer import models
from oscar.test.helpers import create_product
from tests.unit.offer import OfferTest


class PercentageDiscountBenefitTest(OfferTest):

    def setUp(self):
        super(PercentageDiscountBenefitTest, self).setUp()
        self.benefit = models.PercentageDiscountBenefit(range=self.range, type="Percentage", value=Decimal('15.00'))
        self.item = create_product(price=Decimal('5.00'))
        self.original_offer_rounding_function = getattr(settings, 'OSCAR_OFFER_ROUNDING_FUNCTION', None)
        if self.original_offer_rounding_function is not None:
            delattr(settings, 'OSCAR_OFFER_ROUNDING_FUNCTION')

    def tearDown(self):
        super(PercentageDiscountBenefitTest, self).tearDown()
        if self.original_offer_rounding_function is not None:
            settings.OSCAR_OFFER_ROUNDING_FUNCTION = self.original_offer_rounding_function

    def test_no_discount_for_empty_basket(self):
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))

    def test_no_discount_for_not_discountable_product(self):
        self.item.is_discountable = False
        self.item.save()
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))

    def test_discount_for_single_item_basket(self):
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('0.15') * Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket(self):
        self.basket.add_product(self.item, 3)
        self.assertEquals(Decimal('3') * Decimal('0.15') * Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket_with_max_affected_items_set(self):
        self.basket.add_product(self.item, 3)
        self.benefit.max_affected_items = 1
        self.assertEquals(Decimal('0.15') * Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_can_only_be_applied_once(self):
        self.basket.add_product(self.item, 3)
        self.benefit.apply(self.basket)
        second_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('0.00'), second_discount)

    def test_discount_can_be_applied_several_times_when_max_is_set(self):
        self.basket.add_product(self.item, 3)
        self.benefit.max_affected_items = 1
        for i in range(1, 4):
            self.assertTrue(self.benefit.apply(self.basket) > 0)


class AbsoluteDiscountBenefitTest(OfferTest):

    def setUp(self):
        super(AbsoluteDiscountBenefitTest, self).setUp()
        self.benefit = models.AbsoluteDiscountBenefit(
            range=self.range, type="Absolute", value=Decimal('10.00'))
        self.item = create_product(price=Decimal('5.00'))
        self.original_offer_rounding_function = getattr(settings, 'OSCAR_OFFER_ROUNDING_FUNCTION', None)
        if self.original_offer_rounding_function is not None:
            delattr(settings, 'OSCAR_OFFER_ROUNDING_FUNCTION')

    def tearDown(self):
        super(AbsoluteDiscountBenefitTest, self).tearDown()
        if self.original_offer_rounding_function is not None:
            settings.OSCAR_OFFER_ROUNDING_FUNCTION = self.original_offer_rounding_function

    def test_no_discount_for_empty_basket(self):
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))

    def test_no_discount_for_not_discountable_product(self):
        self.item.is_discountable = False
        self.item.save()
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))

    def test_discount_for_single_item_basket(self):
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket(self):
        self.basket.add_product(self.item, 3)
        self.assertEquals(Decimal('10.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket_with_max_affected_items_set(self):
        self.basket.add_product(self.item, 3)
        self.benefit.max_affected_items = 1
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_can_only_be_applied_once(self):
        # Add 3 items to make total 15.00
        self.basket.add_product(self.item, 3)
        first_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('10.00'), first_discount)

        second_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('5.00'), second_discount)

    def test_absolute_does_not_consume_twice(self):
        product = create_product(Decimal('25000'))
        rng = models.Range.objects.create(name='Dummy')
        rng.included_products.add(product)
        condition = models.ValueCondition(range=rng, type='Value', value=Decimal('5000'))
        basket = Basket.objects.create()
        basket.add_product(product, 5)
        benefit = models.AbsoluteDiscountBenefit(range=rng, type='Absolute', value=Decimal('100'))

        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertFalse(condition.is_satisfied(basket))
        self.assertEquals(Decimal('0'), benefit.apply(basket, condition))

    def test_absolute_consumes_all(self):
        product1 = create_product(Decimal('150'))
        product2 = create_product(Decimal('300'))
        product3 = create_product(Decimal('300'))
        rng = models.Range.objects.create(name='Dummy')
        rng.included_products.add(product1)
        rng.included_products.add(product2)
        rng.included_products.add(product3)

        condition = models.ValueCondition(range=rng, type='Value', value=Decimal('500'))

        basket = Basket.objects.create()
        basket.add_product(product1, 1)
        basket.add_product(product2, 1)
        basket.add_product(product3, 1)

        benefit = models.AbsoluteDiscountBenefit(range=rng, type='Absolute', value=Decimal('100'))
        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('0'), benefit.apply(basket, condition))

    def test_absolute_applies_line_discount(self):
        product = create_product(Decimal('500'))
        rng = models.Range.objects.create(name='Dummy')
        rng.included_products.add(product)

        condition = models.ValueCondition(range=rng, type='Value', value=Decimal('500'))
        basket = Basket.objects.create()
        basket.add_product(product, 1)

        benefit = models.AbsoluteDiscountBenefit(range=rng, type='Absolute', value=Decimal('100'))

        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('100'), basket.all_lines()[0]._discount)

    def test_discount_is_applied_to_lines(self):
        condition = models.CountCondition.objects.create(
            range=self.range, type="Count", value=1)
        self.basket.add_product(self.item, 1)
        self.benefit.apply(self.basket, condition)
        self.assertTrue(self.basket.all_lines()[0].has_discount)


class MultibuyDiscountBenefitTest(OfferTest):

    def setUp(self):
        super(MultibuyDiscountBenefitTest, self).setUp()
        self.benefit = models.MultibuyDiscountBenefit(range=self.range, type="Multibuy", value=1)
        self.item = create_product(price=Decimal('5.00'))

    def test_no_discount_for_empty_basket(self):
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))

    def test_discount_for_single_item_basket(self):
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket(self):
        self.basket.add_product(self.item, 3)
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))

    def test_no_discount_for_not_discountable_product(self):
        self.item.is_discountable = False
        self.item.save()
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))

    def test_discount_does_not_consume_item_if_in_condition_range(self):
        self.basket.add_product(self.item, 1)
        first_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('5.00'), first_discount)
        second_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('5.00'), second_discount)

    def test_product_does_consume_item_if_not_in_condition_range(self):
        # Set up condition using a different range from benefit
        range = models.Range.objects.create(name="Small range")
        other_product = create_product(price=Decimal('15.00'))
        range.included_products.add(other_product)
        cond = models.ValueCondition(range=range, type="Value", value=Decimal('10.00'))

        self.basket.add_product(self.item, 1)
        self.benefit.apply(self.basket, cond)
        line = self.basket.all_lines()[0]
        self.assertEqual(line.quantity_without_discount, 0)

    def test_condition_consumes_most_expensive_lines_first(self):
        for i in range(10, 0, -1):
            product = create_product(price=Decimal(i), title='%i'%i, upc='upc_%i' % i)
            self.basket.add_product(product, 1)

        condition = models.CountCondition(range=self.range, type="Count", value=2)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 1 and 10
        first_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('1.00'), first_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 2 and 9
        second_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('2.00'), second_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 3 and 8
        third_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('3.00'), third_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 4 and 7
        fourth_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('4.00'), fourth_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 5 and 6
        fifth_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('5.00'), fifth_discount)

        # end of items (one not discounted item in basket)
        self.assertFalse(condition.is_satisfied(self.basket))

    def test_condition_consumes_most_expensive_lines_first_when_products_are_repeated(self):
        for i in range(5, 0, -1):
            product = create_product(price=Decimal(i), title='%i'%i, upc='upc_%i' % i)
            self.basket.add_product(product, 2)

        condition = models.CountCondition(range=self.range, type="Count", value=2)

        # initial basket: [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 1 and 5
        first_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('1.00'), first_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 1 and 5
        second_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('1.00'), second_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 2 and 4
        third_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('2.00'), third_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 2 and 4
        third_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('2.00'), third_discount)

        self.assertTrue(condition.is_satisfied(self.basket))
        # consume 3 and 3
        third_discount = self.benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('3.00'), third_discount)

        # end of items (one not discounted item in basket)
        self.assertFalse(condition.is_satisfied(self.basket))

    def test_products_with_no_stockrecord_are_handled_ok(self):
        self.basket.add_product(self.item, 3)
        self.basket.add_product(create_product())
        condition = models.CountCondition(range=self.range, type="Count", value=3)
        self.benefit.apply(self.basket, condition)


class FixedPriceBenefitTest(OfferTest):

    def setUp(self):
        super(FixedPriceBenefitTest, self).setUp()
        self.benefit = models.FixedPriceBenefit(range=self.range, type="FixedPrice", value=Decimal('10.00'))

    def test_correct_discount_for_count_condition(self):
        products = [create_product(Decimal('7.00')),
                    create_product(Decimal('8.00')),
                    create_product(Decimal('12.00'))]

        # Create range that includes the products
        range = models.Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
        condition = models.CountCondition(range=range, type="Count", value=3)

        # Create basket that satisfies condition but with one extra product
        basket = Basket.objects.create()
        [basket.add_product(p, 2) for p in products]

        benefit = models.FixedPriceBenefit(range=range, type="FixedPrice", value=Decimal('20.00'))
        self.assertEquals(Decimal('2.00'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('12.00'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('0.00'), benefit.apply(basket, condition))

    def test_correct_discount_is_returned(self):
        products = [create_product(Decimal('8.00')), create_product(Decimal('4.00'))]
        range = models.Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
            range.included_products.add(product)

        basket = Basket.objects.create()
        [basket.add_product(p) for p in products]

        condition = models.CoverageCondition(range=range, type="Coverage", value=2)
        discount = self.benefit.apply(basket, condition)
        self.assertEquals(Decimal('2.00'), discount)

    def test_no_discount_when_product_not_discountable(self):
        product = create_product(Decimal('18.00'))
        product.is_discountable = False
        product.save()

        product_range = models.Range.objects.create(name="Dummy range")
        product_range.included_products.add(product)

        basket = Basket.objects.create()
        basket.add_product(product)

        condition = models.CoverageCondition(range=product_range, type="Coverage", value=1)
        discount = self.benefit.apply(basket, condition)
        self.assertEquals(Decimal('0.00'), discount)

    def test_no_discount_is_returned_when_value_is_greater_than_product_total(self):
        products = [create_product(Decimal('4.00')), create_product(Decimal('4.00'))]
        range = models.Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
            range.included_products.add(product)

        basket = Basket.objects.create()
        [basket.add_product(p) for p in products]

        condition = models.CoverageCondition(range=range, type="Coverage", value=2)
        discount = self.benefit.apply(basket, condition)
        self.assertEquals(Decimal('0.00'), discount)

    def test_discount_when_more_products_than_required(self):
        products = [create_product(Decimal('4.00')),
                    create_product(Decimal('8.00')),
                    create_product(Decimal('12.00'))]

        # Create range that includes the products
        range = models.Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
        condition = models.CoverageCondition(range=range, type="Coverage", value=3)

        # Create basket that satisfies condition but with one extra product
        basket = Basket.objects.create()
        [basket.add_product(p) for p in products]
        basket.add_product(products[0])

        benefit = models.FixedPriceBenefit(range=range, type="FixedPrice", value=Decimal('20.00'))
        discount = benefit.apply(basket, condition)
        self.assertEquals(Decimal('4.00'), discount)

    def test_discount_when_applied_twice(self):
        products = [create_product(Decimal('4.00')),
                    create_product(Decimal('8.00')),
                    create_product(Decimal('12.00'))]

        # Create range that includes the products
        range = models.Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
        condition = models.CoverageCondition(range=range, type="Coverage", value=3)

        # Create basket that satisfies condition but with one extra product
        basket = Basket.objects.create()
        [basket.add_product(p, 2) for p in products]

        benefit = models.FixedPriceBenefit(range=range, type="FixedPrice", value=Decimal('20.00'))
        first_discount = benefit.apply(basket, condition)
        self.assertEquals(Decimal('4.00'), first_discount)
        second_discount = benefit.apply(basket, condition)
        self.assertEquals(Decimal('4.00'), second_discount)
