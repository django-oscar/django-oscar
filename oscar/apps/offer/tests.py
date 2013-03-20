from decimal import Decimal, ROUND_UP
import datetime

from django.conf import settings
from django.test import TestCase

from oscar.apps.offer.models import (Range, CountCondition, ValueCondition,
                                     CoverageCondition, ConditionalOffer,
                                     PercentageDiscountBenefit, FixedPriceBenefit,
                                     MultibuyDiscountBenefit, AbsoluteDiscountBenefit)
from oscar.apps.offer.utils import Applicator
from oscar.apps.basket.models import Basket
from oscar.test.helpers import create_product


class CustomConditionalOffer(ConditionalOffer):
    def get_max_applications(self):
        return 3


class ApplicatorTest(TestCase):

    def test_max_application_limit(self):
        rng = Range.objects.create(name="All products range", includes_all_products=True)
        basket = Basket.objects.create()
        item = create_product(price=Decimal('100'))
        basket.add_product(item, 5)
        cond = ValueCondition(range=rng, type="Value", value=Decimal('100.00'))
        benefit = MultibuyDiscountBenefit(range=rng, type="Multibuy")
        offer = CustomConditionalOffer(id='test', condition=cond, benefit=benefit)
        applicator = Applicator()
        discounts = applicator.get_basket_discounts(basket, [offer])
        discount = discounts['test']
        self.assertEquals(discount['freq'], 3)
        self.assertEquals(discount['discount'], Decimal('300'))


class WholeSiteRangeWithGlobalBlacklistTest(TestCase):

    def setUp(self):
        self.range = Range.objects.create(name="All products", includes_all_products=True)

    def tearDown(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = None

    def test_blacklisting_prevents_products_being_in_range(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = lambda p: True
        prod = create_product()
        self.assertFalse(self.range.contains_product(prod))

    def test_blacklisting_can_use_product_class(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = lambda p: p.product_class.name == 'giftcard'
        prod = create_product(product_class="giftcard")
        self.assertFalse(self.range.contains_product(prod))

    def test_blacklisting_doesnt_exlude_everything(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = lambda p: p.product_class.name == 'giftcard'
        prod = create_product(product_class="book")
        self.assertTrue(self.range.contains_product(prod))


class WholeSiteRangeTest(TestCase):

    def setUp(self):
        self.range = Range.objects.create(name="All products", includes_all_products=True)
        self.prod = create_product()

    def test_all_products_range(self):
        self.assertTrue(self.range.contains_product(self.prod))

    def test_all_products_range_with_exception(self):
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))

    def test_whitelisting(self):
        self.range.included_products.add(self.prod)
        self.assertTrue(self.range.contains_product(self.prod))

    def test_blacklisting(self):
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))


class PartialRangeTest(TestCase):

    def setUp(self):
        self.range = Range.objects.create(name="All products", includes_all_products=False)
        self.prod = create_product()

    def test_empty_list(self):
        self.assertFalse(self.range.contains_product(self.prod))

    def _test_included_classes(self):
        self.range.classes.add(self.prod.product_class)
        self.assertTrue(self.range.contains_product(self.prod))

    def _test_included_class_with_exception(self):
        self.range.classes.add(self.prod.product_class)
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))


class OfferTest(TestCase):
    def setUp(self):
        self.range = Range.objects.create(name="All products range", includes_all_products=True)
        self.basket = Basket.objects.create()


class CountConditionTest(OfferTest):

    def setUp(self):
        super(CountConditionTest, self).setUp()
        self.cond = CountCondition(range=self.range, type="Count", value=2)

    def test_empty_basket_fails_condition(self):
        self.assertFalse(self.cond.is_satisfied(self.basket))

    def test_matching_quantity_basket_passes_condition(self):
        self.basket.add_product(create_product(), 2)
        self.assertTrue(self.cond.is_satisfied(self.basket))

    def test_greater_quantity_basket_passes_condition(self):
        self.basket.add_product(create_product(), 3)
        self.assertTrue(self.cond.is_satisfied(self.basket))

    def test_consumption(self):
        self.basket.add_product(create_product(), 3)
        self.cond.consume_items(self.basket)
        self.assertEquals(1, self.basket.all_lines()[0].quantity_without_discount)

    def test_is_satisfied_accounts_for_consumed_items(self):
        self.basket.add_product(create_product(), 3)
        self.cond.consume_items(self.basket)
        self.assertFalse(self.cond.is_satisfied(self.basket))

    def test_count_condition_is_applied_multpile_times(self):
        benefit = MultibuyDiscountBenefit(range=self.range, type="Multibuy")
        for i in range(10):
            self.basket.add_product(create_product(price=Decimal('5.00'), upc='upc_%i' % i), 1)
        product_range = Range.objects.create(name="All products", includes_all_products=True)
        condition = CountCondition(range=product_range, type="Count", value=2)

        first_discount = benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('5.00'), first_discount)

        second_discount = benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('5.00'), second_discount)


class ValueConditionTest(OfferTest):
    def setUp(self):
        super(ValueConditionTest, self).setUp()
        self.cond = ValueCondition(range=self.range, type="Value", value=Decimal('10.00'))
        self.item = create_product(price=Decimal('5.00'))
        self.expensive_item = create_product(price=Decimal('15.00'))

    def test_empty_basket_fails_condition(self):
        self.assertFalse(self.cond.is_satisfied(self.basket))

    def test_less_value_basket_fails_condition(self):
        self.basket.add_product(self.item, 1)
        self.assertFalse(self.cond.is_satisfied(self.basket))

    def test_matching_basket_passes_condition(self):
        self.basket.add_product(self.item, 2)
        self.assertTrue(self.cond.is_satisfied(self.basket))

    def test_greater_than_basket_passes_condition(self):
        self.basket.add_product(self.item, 3)
        self.assertTrue(self.cond.is_satisfied(self.basket))

    def test_consumption(self):
        self.basket.add_product(self.item, 3)
        self.cond.consume_items(self.basket)
        self.assertEquals(1, self.basket.all_lines()[0].quantity_without_discount)

    def test_consumption_with_high_value_product(self):
        self.basket.add_product(self.expensive_item, 1)
        self.cond.consume_items(self.basket)
        self.assertEquals(0, self.basket.all_lines()[0].quantity_without_discount)

    def test_is_consumed_respects_quantity_consumed(self):
        self.basket.add_product(self.expensive_item, 1)
        self.assertTrue(self.cond.is_satisfied(self.basket))
        self.cond.consume_items(self.basket)
        self.assertFalse(self.cond.is_satisfied(self.basket))


class CoverageConditionTest(TestCase):

    def setUp(self):
        self.products = [create_product(Decimal('5.00')), create_product(Decimal('10.00'))]
        self.range = Range.objects.create(name="Some products")
        for product in self.products:
            self.range.included_products.add(product)
            self.range.included_products.add(product)

        self.basket = Basket.objects.create()
        self.cond = CoverageCondition(range=self.range, type="Coverage", value=2)

    def test_empty_basket_fails(self):
        self.assertFalse(self.cond.is_satisfied(self.basket))

    def test_single_item_fails(self):
        self.basket.add_product(self.products[0])
        self.assertFalse(self.cond.is_satisfied(self.basket))

    def test_duplicate_item_fails(self):
        self.basket.add_product(self.products[0])
        self.basket.add_product(self.products[0])
        self.assertFalse(self.cond.is_satisfied(self.basket))

    def test_covering_items_pass(self):
        self.basket.add_product(self.products[0])
        self.basket.add_product(self.products[1])
        self.assertTrue(self.cond.is_satisfied(self.basket))

    def test_covering_items_are_consumed(self):
        self.basket.add_product(self.products[0])
        self.basket.add_product(self.products[1])
        self.cond.consume_items(self.basket)
        self.assertEquals(0, self.basket.num_items_without_discount)

    def test_consumed_items_checks_affected_items(self):
        # Create new offer
        range = Range.objects.create(name="All products", includes_all_products=True)
        cond = CoverageCondition(range=range, type="Coverage", value=2)

        # Get 4 distinct products in the basket
        self.products.extend([create_product(Decimal('15.00')), create_product(Decimal('20.00'))])

        for product in self.products:
            self.basket.add_product(product)

        self.assertTrue(cond.is_satisfied(self.basket))
        cond.consume_items(self.basket)
        self.assertEquals(2, self.basket.num_items_without_discount)

        self.assertTrue(cond.is_satisfied(self.basket))
        cond.consume_items(self.basket)
        self.assertEquals(0, self.basket.num_items_without_discount)


class PercentageDiscountBenefitTest(OfferTest):

    def setUp(self):
        super(PercentageDiscountBenefitTest, self).setUp()
        self.benefit = PercentageDiscountBenefit(range=self.range, type="Percentage", value=Decimal('15.00'))
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
        self.benefit = AbsoluteDiscountBenefit(range=self.range, type="Absolute", value=Decimal('10.00'))
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

    def test_discount_for_single_item_basket(self):
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket(self):
        self.basket.add_product(self.item, 3)
        self.assertEquals(Decimal('10.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket_with_max_affected_items_set(self):
        self.basket.add_product(self.item, 3)
        self.benefit.max_affected_items = 1
        total_price = self.basket.total_incl_tax_excl_discounts
        product_after_discount = (((Decimal(self.benefit.value) / total_price) * Decimal('5'))
                                  .quantize(Decimal('1.', ROUND_UP)))
        self.assertEquals(product_after_discount, self.benefit.apply(self.basket))

    def test_discount_can_only_be_applied_once(self):
        # Add 3 items to make total 15.00
        self.basket.add_product(self.item, 3)
        first_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('10.00'), first_discount)

        second_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('0.00'), second_discount)

    def test_absolute_consumes_all(self):
        product1 = create_product(Decimal('150'))
        product2 = create_product(Decimal('300'))
        product3 = create_product(Decimal('300'))
        rng = Range.objects.create(name='Dummy')
        rng.included_products.add(product1)
        rng.included_products.add(product2)
        rng.included_products.add(product3)
        condition = ValueCondition(range=rng, type='Value', value=Decimal('500'))
        basket = Basket.objects.create()
        basket.add_product(product1, 1)
        basket.add_product(product2, 1)
        basket.add_product(product3, 1)
        benefit = AbsoluteDiscountBenefit(range=rng, type='Absolute', value=Decimal('100'))
        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('0'), benefit.apply(basket, condition))

    def test_absolute_applies_line_discount(self):
        product = create_product(Decimal('500'))
        rng = Range.objects.create(name='Dummy')
        rng.included_products.add(product)
        condition = ValueCondition(range=rng, type='Value', value=Decimal('500'))
        basket = Basket.objects.create()
        basket.add_product(product, 1)
        benefit = AbsoluteDiscountBenefit(range=rng, type='Absolute', value=Decimal('100'))
        self.assertTrue(condition.is_satisfied(basket))
        self.assertEquals(Decimal('100'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('100'), basket.all_lines()[0]._discount)


class MultibuyDiscountBenefitTest(OfferTest):

    def setUp(self):
        super(MultibuyDiscountBenefitTest, self).setUp()
        self.benefit = MultibuyDiscountBenefit(range=self.range, type="Multibuy", value=1)
        self.item = create_product(price=Decimal('5.00'))

    def test_no_discount_for_empty_basket(self):
        self.assertEquals(Decimal('0.00'), self.benefit.apply(self.basket))

    def test_discount_for_single_item_basket(self):
        self.basket.add_product(self.item, 1)
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_for_multi_item_basket(self):
        self.basket.add_product(self.item, 3)
        self.assertEquals(Decimal('5.00'), self.benefit.apply(self.basket))

    def test_discount_does_not_consume_item_if_in_condition_range(self):
        self.basket.add_product(self.item, 1)
        first_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('5.00'), first_discount)
        second_discount = self.benefit.apply(self.basket)
        self.assertEquals(Decimal('5.00'), second_discount)

    def test_product_does_consume_item_if_not_in_condition_range(self):
        # Set up condition using a different range from benefit
        range = Range.objects.create(name="Small range")
        other_product = create_product(price=Decimal('15.00'))
        range.included_products.add(other_product)
        cond = ValueCondition(range=range, type="Value", value=Decimal('10.00'))

        self.basket.add_product(self.item, 1)
        self.benefit.apply(self.basket, cond)
        line = self.basket.all_lines()[0]
        self.assertEqual(line.quantity_without_discount, 0)

    def test_condition_consumes_most_expensive_lines_first(self):
        for i in range(10, 0, -1):
            product = create_product(price=Decimal(i), title='%i' % i, upc='upc_%i' % i)
            self.basket.add_product(product, 1)

        condition = CountCondition(range=self.range, type="Count", value=2)

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
            product = create_product(price=Decimal(i), title='%i' % i, upc='upc_%i' % i)
            self.basket.add_product(product, 2)

        condition = CountCondition(range=self.range, type="Count", value=2)

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
        condition = CountCondition(range=self.range, type="Count", value=3)
        self.benefit.apply(self.basket, condition)

    def test_correct_products_are_consumed_when_ranges_overlap(self):
        product1 = create_product(price=Decimal(10), title='P1', upc='upc_1')
        product2 = create_product(price=Decimal(20), title='P2', upc='upc_2')
        product3 = create_product(price=Decimal(30), title='P3', upc='upc_3')
        range1 = Range.objects.create(name="Range1")
        range1.included_products.add(product1)
        range1.included_products.add(product2)
        self.basket.add_product(product1, 2)
        self.basket.add_product(product2, 1)
        self.basket.add_product(product3, 1)
        condition = CountCondition(range=range1, type="Count", value=2)
        benefit = MultibuyDiscountBenefit(range=range1, type="Multibuy", value=1)
        self.assertTrue(condition.is_satisfied(self.basket))
        first_discount = benefit.apply(self.basket, condition=condition)
        self.assertEquals(Decimal('10'), first_discount)
        # verify that one product1 is consumed by benefit
        line1 = [l for l in self.basket.all_lines() if l.product == product1][0]
        self.assertEquals(1, line1._affected_quantity)
        # and one product2 is consumed by the condition
        line2 = [l for l in self.basket.all_lines() if l.product == product2][0]
        self.assertEquals(1, line2._affected_quantity)
        line3 = [l for l in self.basket.all_lines() if l.product == product3][0]
        self.assertEquals(0, line3._affected_quantity)


class FixedPriceBenefitTest(OfferTest):

    def setUp(self):
        super(FixedPriceBenefitTest, self).setUp()
        self.benefit = FixedPriceBenefit(range=self.range, type="FixedPrice", value=Decimal('10.00'))

    def test_correct_discount_for_count_condition(self):
        products = [create_product(Decimal('7.00')),
                    create_product(Decimal('8.00')),
                    create_product(Decimal('12.00'))]

        # Create range that includes the products
        range = Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
        condition = CountCondition(range=range, type="Count", value=3)

        # Create basket that satisfies condition but with one extra product
        basket = Basket.objects.create()
        [basket.add_product(p, 2) for p in products]

        benefit = FixedPriceBenefit(range=range, type="FixedPrice", value=Decimal('20.00'))
        self.assertEquals(Decimal('2.00'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('12.00'), benefit.apply(basket, condition))
        self.assertEquals(Decimal('0.00'), benefit.apply(basket, condition))

    def test_correct_discount_is_returned(self):
        products = [create_product(Decimal('8.00')), create_product(Decimal('4.00'))]
        range = Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
            range.included_products.add(product)

        basket = Basket.objects.create()
        [basket.add_product(p) for p in products]

        condition = CoverageCondition(range=range, type="Coverage", value=2)
        discount = self.benefit.apply(basket, condition)
        self.assertEquals(Decimal('2.00'), discount)

    def test_no_discount_is_returned_when_value_is_greater_than_product_total(self):
        products = [create_product(Decimal('4.00')), create_product(Decimal('4.00'))]
        range = Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
            range.included_products.add(product)

        basket = Basket.objects.create()
        [basket.add_product(p) for p in products]

        condition = CoverageCondition(range=range, type="Coverage", value=2)
        discount = self.benefit.apply(basket, condition)
        self.assertEquals(Decimal('0.00'), discount)

    def test_discount_when_more_products_than_required(self):
        products = [create_product(Decimal('4.00')),
                    create_product(Decimal('8.00')),
                    create_product(Decimal('12.00'))]

        # Create range that includes the products
        range = Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
        condition = CoverageCondition(range=range, type="Coverage", value=3)

        # Create basket that satisfies condition but with one extra product
        basket = Basket.objects.create()
        [basket.add_product(p) for p in products]
        basket.add_product(products[0])

        benefit = FixedPriceBenefit(range=range, type="FixedPrice", value=Decimal('20.00'))
        discount = benefit.apply(basket, condition)
        self.assertEquals(Decimal('4.00'), discount)

    def test_discount_when_applied_twice(self):
        products = [create_product(Decimal('4.00')),
                    create_product(Decimal('8.00')),
                    create_product(Decimal('12.00'))]

        # Create range that includes the products
        range = Range.objects.create(name="Dummy range")
        for product in products:
            range.included_products.add(product)
        condition = CoverageCondition(range=range, type="Coverage", value=3)

        # Create basket that satisfies condition but with one extra product
        basket = Basket.objects.create()
        [basket.add_product(p, 2) for p in products]

        benefit = FixedPriceBenefit(range=range, type="FixedPrice", value=Decimal('20.00'))
        first_discount = benefit.apply(basket, condition)
        self.assertEquals(Decimal('4.00'), first_discount)
        second_discount = benefit.apply(basket, condition)
        self.assertEquals(Decimal('4.00'), second_discount)


class ConditionalOfferTest(TestCase):

    def test_is_active(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 01, 10)
        end = datetime.date(2011, 02, 01)
        offer = ConditionalOffer(start_date=start, end_date=end)
        self.assertTrue(offer.is_active(test))

    def test_is_inactive(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 03, 10)
        end = datetime.date(2011, 02, 01)
        offer = ConditionalOffer(start_date=start, end_date=end)
        self.assertFalse(offer.is_active(test))
