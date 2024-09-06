# -*- coding: utf-8 -*-
from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.basket.models import Basket
from oscar.apps.catalogue.models import Option
from oscar.apps.partner import availability, prices, strategy
from oscar.test import factories
from oscar.test.factories import (
    BasketFactory,
    BasketLineAttributeFactory,
    OptionFactory,
    ProductFactory,
)


class TestANewBasket(TestCase):
    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()

    def test_has_zero_lines(self):
        self.assertEqual(0, self.basket.num_lines)

    def test_has_zero_items(self):
        self.assertEqual(0, self.basket.num_items)

    def test_doesnt_contain_vouchers(self):
        # assert no exception on unsaved basket
        self.assertFalse(Basket().contains_a_voucher)
        self.assertFalse(self.basket.contains_a_voucher)

    def test_can_be_edited(self):
        self.assertTrue(self.basket.can_be_edited)

    def test_is_empty(self):
        self.assertTrue(self.basket.is_empty)

    def test_is_not_submitted(self):
        self.assertFalse(self.basket.is_submitted)

    def test_has_no_applied_offers(self):
        self.assertEqual({}, self.basket.applied_offers())

    def test_is_tax_unknown(self):
        self.assertTrue(self.basket.is_empty)
        self.assertFalse(self.basket.is_tax_known)


class TestBasketLine(TestCase):
    def test_description(self):
        basket = BasketFactory()
        product = ProductFactory(title="A product")
        basket.add_product(product)

        line = basket.all_lines()[0]
        self.assertEqual(line.description, "A product")

    def test_description_with_attributes(self):
        basket = BasketFactory()
        product = ProductFactory(title="A product")
        basket.add_product(product)

        # pylint: disable=no-member
        line = basket.lines.first()
        BasketLineAttributeFactory(line=line, value="\u2603", option__name="with")
        self.assertEqual(line.description, "A product (with = '\u2603')")

    def test_create_line_reference(self):
        basket = BasketFactory()
        product = ProductFactory(title="A product")
        option = OptionFactory(name="product_option", code="product_option")
        option_product = ProductFactory(title="Asunción")
        options = [{"option": option, "value": str(option_product)}]
        basket.add_product(product, options=options)

    def test_basket_lines_queryset_is_ordered(self):
        # This is needed to make sure a formset is not performing the query
        # again with an order_by clause (losing all calculated discounts)
        basket = BasketFactory()
        product = ProductFactory(title="A product")
        another_product = ProductFactory(title="Another product")
        basket.add_product(product)
        basket.add_product(another_product)
        queryset = basket.all_lines()
        self.assertTrue(queryset.ordered)

    def test_line_tax_for_zero_tax_strategies(self):
        basket = Basket()
        basket.strategy = strategy.Default()
        product = factories.create_product()
        # Tax for the default strategy will be 0
        factories.create_stockrecord(product, price=D("75.00"), num_in_stock=10)
        basket.add(product, 1)

        self.assertEqual(basket.all_lines()[0].line_tax, D("0"))

    def test_line_tax_for_unknown_tax_strategies(self):
        class UnknownTaxStrategy(strategy.Default):
            """A test strategy where the tax is not known"""

            def pricing_policy(self, product, stockrecord):
                return prices.FixedPrice("GBP", stockrecord.price, tax=None)

        basket = Basket()
        basket.strategy = UnknownTaxStrategy()
        product = factories.create_product()
        factories.create_stockrecord(product, num_in_stock=10)
        basket.add(product, 1)

        self.assertEqual(basket.all_lines()[0].line_tax, None)


class TestAddingAProductToABasket(TestCase):
    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.product = factories.create_product()
        self.record = factories.create_stockrecord(
            currency="GBP", product=self.product, price=D("10.00")
        )
        self.purchase_info = factories.create_purchase_info(self.record)
        self.basket.add(self.product)

    def test_creates_a_line(self):
        self.assertEqual(1, self.basket.num_lines)

    def test_sets_line_prices(self):
        line = self.basket.all_lines()[0]
        self.assertEqual(line.price_incl_tax, self.purchase_info.price.incl_tax)
        self.assertEqual(line.price_excl_tax, self.purchase_info.price.excl_tax)

    def test_adding_negative_quantity(self):
        self.assertEqual(1, self.basket.num_lines)
        self.basket.add(self.product, quantity=4)
        self.assertEqual(5, self.basket.line_quantity(self.product, self.record))
        self.basket.add(self.product, quantity=-10)
        self.assertEqual(0, self.basket.line_quantity(self.product, self.record))

    def test_means_another_currency_product_cannot_be_added(self):
        product = factories.create_product()
        factories.create_stockrecord(currency="USD", product=product, price=D("20.00"))
        with self.assertRaises(ValueError):
            self.basket.add(product)

    def test_cannot_add_a_product_without_price(self):
        product = factories.create_product(price=None)
        with self.assertRaises(ValueError):
            self.basket.add(product)

    def test_is_tax_known(self):
        self.assertTrue(self.basket.is_tax_known)


class TestANonEmptyBasket(TestCase):
    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.product = factories.create_product()
        self.record = factories.create_stockrecord(self.product, price=D("10.00"))
        self.purchase_info = factories.create_purchase_info(self.record)
        self.basket.add(self.product, 10)

    def test_can_be_flushed(self):
        self.basket.flush()
        self.assertEqual(self.basket.num_items, 0)

    def test_returns_correct_product_quantity(self):
        # assert no exception on unsaved basket
        self.assertEqual(0, Basket().product_quantity(self.product))
        self.assertEqual(10, self.basket.product_quantity(self.product))

    def test_returns_correct_line_quantity_for_unsaved_basket(self):
        # assert no exception on unsaved basket
        self.assertEqual(0, Basket().line_quantity(self.product, self.record))

    def test_returns_correct_line_quantity_for_existing_product_and_stockrecord(self):
        self.assertEqual(10, self.basket.line_quantity(self.product, self.record))

    def test_returns_zero_line_quantity_for_alternative_stockrecord(self):
        record = factories.create_stockrecord(self.product, price=D("5.00"))
        self.assertEqual(0, self.basket.line_quantity(self.product, record))

    def test_returns_zero_line_quantity_for_missing_product_and_stockrecord(self):
        product = factories.create_product()
        record = factories.create_stockrecord(product, price=D("5.00"))
        self.assertEqual(0, self.basket.line_quantity(product, record))

    def test_returns_correct_quantity_for_existing_product_and_stockrecord_and_options(
        self,
    ):
        product = factories.create_product()
        record = factories.create_stockrecord(product, price=D("5.00"))
        option = Option.objects.create(name="Message")
        options = [{"option": option, "value": "2"}]

        self.basket.add(product, options=options)
        self.assertEqual(0, self.basket.line_quantity(product, record))
        self.assertEqual(1, self.basket.line_quantity(product, record, options))

    def test_total_sums_product_totals(self):
        product = factories.create_product()
        factories.create_stockrecord(product, price=D("5.00"))
        self.basket.add(product, 1)
        self.assertEqual(self.basket.total_excl_tax, 105)

    def test_totals_for_free_products(self):
        basket = Basket()
        basket.strategy = strategy.Default()
        # Add a zero-priced product to the basket
        product = factories.create_product()
        factories.create_stockrecord(product, price=D("0.00"), num_in_stock=10)
        basket.add(product, 1)

        self.assertEqual(len(basket.all_lines()), 1)
        self.assertEqual(basket.total_excl_tax, 0)
        self.assertEqual(basket.total_incl_tax, 0)

    def test_basket_prices_calculation_for_unavailable_pricing(self):
        new_product = factories.create_product()
        factories.create_stockrecord(new_product, price=D("5.00"))
        self.basket.add(new_product, 1)

        class UnavailableProductStrategy(strategy.Default):
            """A test strategy that makes a specific product unavailable"""

            def availability_policy(self, product, stockrecord):
                if product == new_product:
                    return availability.Unavailable()
                return super().availability_policy(product, stockrecord)

            def pricing_policy(self, product, stockrecord):
                if product == new_product:
                    return prices.Unavailable()
                return super().pricing_policy(product, stockrecord)

        self.basket.strategy = UnavailableProductStrategy()
        line = self.basket.all_lines()[1]
        self.assertEqual(
            line.get_warning(), "'D\xf9\uff4d\u03fb\u03d2 title' is no longer available"
        )
        self.assertIsNone(line.line_price_excl_tax)
        self.assertIsNone(line.line_price_incl_tax)
        self.assertIsNone(line.line_price_excl_tax_incl_discounts)
        self.assertIsNone(line.line_price_incl_tax_incl_discounts)
        self.assertIsNone(line.line_tax)
        self.assertEqual(self.basket.total_excl_tax, 100)
        self.assertEqual(self.basket.total_incl_tax, 100)
        self.assertEqual(self.basket.total_excl_tax_excl_discounts, 100)
        self.assertEqual(self.basket.total_incl_tax_excl_discounts, 100)

    def test_max_allowed_quantity(self):
        self.basket.add_product(self.product, quantity=3)

        # max allowed here is 7 (20-10+3)
        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=20):
            max_allowed, basket_threshold = self.basket.max_allowed_quantity()
            self.assertEqual(max_allowed, 7)
            self.assertEqual(basket_threshold, 20)

        # but we can also completely disable the threshold
        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=None):
            max_allowed, basket_threshold = self.basket.max_allowed_quantity()
            self.assertEqual(max_allowed, None)
            self.assertEqual(basket_threshold, None)

    def test_is_quantity_allowed(self):
        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=20):
            # assert no exception on unsaved basket
            allowed, message = Basket().is_quantity_allowed(1)
            self.assertTrue(allowed)
            self.assertIsNone(message)
            # 7 or below is possible
            allowed, message = self.basket.is_quantity_allowed(qty=7)
            self.assertTrue(allowed)
            self.assertIsNone(message)
            # but above it's not
            allowed, message = self.basket.is_quantity_allowed(qty=11)
            self.assertFalse(allowed)
            self.assertIsNotNone(message)

        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=None):
            # with the threshold disabled all quantities are possible
            allowed, message = self.basket.is_quantity_allowed(qty=7)
            self.assertTrue(allowed)
            self.assertIsNone(message)
            allowed, message = self.basket.is_quantity_allowed(qty=5000)
            self.assertTrue(allowed)
            self.assertIsNone(message)


class TestMergingTwoBaskets(TestCase):
    def setUp(self):
        self.product = factories.create_product()
        self.record = factories.create_stockrecord(self.product, price=D("10.00"))
        self.purchase_info = factories.create_purchase_info(self.record)

        self.main_basket = Basket()
        self.main_basket.strategy = strategy.Default()
        self.main_basket.add(self.product, quantity=2)

        self.merge_basket = Basket()
        self.merge_basket.strategy = strategy.Default()
        self.merge_basket.add(self.product, quantity=1)

        self.main_basket.merge(self.merge_basket)

    def test_doesnt_sum_quantities(self):
        self.assertEqual(1, self.main_basket.num_lines)

    def test_changes_status_of_merge_basket(self):
        self.assertEqual(Basket.MERGED, self.merge_basket.status)


class TestASubmittedBasket(TestCase):
    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.basket.submit()

    def test_has_correct_status(self):
        self.assertTrue(self.basket.is_submitted)

    def test_can_be_edited(self):
        self.assertFalse(self.basket.can_be_edited)


class TestMergingAVoucherBasket(TestCase):
    def test_transfers_vouchers_to_new_basket(self):
        baskets = [factories.BasketFactory(), factories.BasketFactory()]
        voucher = factories.VoucherFactory()
        baskets[0].vouchers.add(voucher)
        baskets[1].merge(baskets[0])

        self.assertEqual(1, baskets[1].vouchers.all().count())
