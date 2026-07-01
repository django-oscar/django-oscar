# pylint: disable=redefined-outer-name
from decimal import Decimal as D
from unittest import mock

import pytest
from django.test import TestCase
from django.utils.timezone import now

from oscar.apps.basket.models import Basket
from oscar.apps.offer import applicator, custom, models
from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.basket import add_product
from tests._site.model_tests_app.models import BasketOwnerCalledBarry

Selector = get_class("partner.strategy", "Selector")


@pytest.fixture
def products_some():
    return [factories.create_product(), factories.create_product()]


@pytest.fixture()
def product_range():
    return factories.RangeFactory()


@pytest.fixture
def range_all():
    return factories.RangeFactory(name="All products range", includes_all_products=True)


@pytest.fixture
def range_some(products_some):
    return factories.RangeFactory(name="Some products", products=products_some)


@pytest.fixture
def count_condition(range_all):
    return models.CountCondition(range=range_all, type="Count", value=2)


@pytest.fixture
def value_condition(range_all):
    return models.ValueCondition(range=range_all, type="Value", value=D("10.00"))


@pytest.fixture
def coverage_condition(range_some):
    return models.CoverageCondition(range=range_some, type="Coverage", value=2)


@pytest.fixture
def empty_basket():
    return factories.create_basket(empty=True)


@pytest.fixture
def partial_basket(empty_basket):
    basket = empty_basket
    add_product(basket)
    return basket


@pytest.fixture
def mock_offer():
    return mock.Mock()


@pytest.mark.django_db
class TestCountCondition:
    @pytest.fixture(autouse=True)
    def setUp(self, mock_offer):
        self.offer = mock_offer

    def test_description(self, count_condition):
        assert count_condition.description

    def test_is_not_satisfied_by_empty_basket(self, count_condition, empty_basket):
        assert count_condition.is_satisfied(self.offer, empty_basket) is False

    def test_not_discountable_product_fails_condition(
        self, count_condition, empty_basket
    ):
        basket = empty_basket
        prod1, prod2 = factories.create_product(), factories.create_product()
        prod2.is_discountable = False
        prod2.save()
        add_product(basket, product=prod1)
        add_product(basket, product=prod2)
        assert count_condition.is_satisfied(self.offer, basket) is False

    def test_empty_basket_fails_partial_condition(self, count_condition, empty_basket):
        assert count_condition.is_partially_satisfied(self.offer, empty_basket) is False

    def test_smaller_quantity_basket_passes_partial_condition(
        self, count_condition, empty_basket
    ):
        basket = empty_basket
        add_product(basket)
        assert count_condition.is_partially_satisfied(self.offer, basket)
        assert count_condition._num_matches == 1

    def test_smaller_quantity_basket_upsell_message(
        self, count_condition, empty_basket
    ):
        basket = empty_basket
        add_product(basket)
        assert "Buy 1 more product from " in count_condition.get_upsell_message(
            self.offer, basket
        )

    def test_matching_quantity_basket_fails_partial_condition(
        self, count_condition, empty_basket
    ):
        basket = empty_basket
        add_product(basket, quantity=2)
        assert count_condition.is_partially_satisfied(self.offer, basket) is False

    def test_matching_quantity_basket_passes_condition(
        self, count_condition, empty_basket
    ):
        basket = empty_basket
        add_product(basket, quantity=2)
        assert count_condition.is_satisfied(self.offer, basket)

    def test_greater_quantity_basket_passes_condition(
        self, count_condition, empty_basket
    ):
        basket = empty_basket
        add_product(basket, quantity=3)
        assert count_condition.is_satisfied(self.offer, basket)

    def test_consumption(self, count_condition, empty_basket):
        basket = empty_basket
        add_product(basket, quantity=3)
        count_condition.consume_items(self.offer, basket, [])
        assert 1 == basket.all_lines()[0].quantity_without_discount

    def test_is_satisfied_accounts_for_consumed_items(
        self, count_condition, empty_basket
    ):
        basket = empty_basket
        add_product(basket, quantity=3)
        count_condition.consume_items(self.offer, basket, [])
        assert count_condition.is_satisfied(self.offer, basket) is False


@pytest.mark.django_db
class TestValueCondition:
    @pytest.fixture(autouse=True)
    def setUp(self, empty_basket, value_condition, mock_offer):
        self.basket = empty_basket
        self.condition = value_condition
        self.offer = mock_offer
        self.item = factories.create_product(price=D("5.00"))
        self.expensive_item = factories.create_product(price=D("15.00"))

    def test_description(self, value_condition):
        assert value_condition.description

    def test_empty_basket_fails_condition(self):
        assert self.condition.is_satisfied(self.offer, self.basket) is False

    def test_empty_basket_fails_partial_condition(self):
        assert self.condition.is_partially_satisfied(self.offer, self.basket) is False

    def test_less_value_basket_fails_condition(self):
        add_product(self.basket, D("5"))
        assert self.condition.is_satisfied(self.offer, self.basket) is False

    def test_not_discountable_item_fails_condition(self):
        product = factories.create_product(is_discountable=False)
        add_product(self.basket, D("15"), product=product)
        assert self.condition.is_satisfied(self.offer, self.basket) is False

    def test_upsell_message(self):
        add_product(self.basket, D("5"))
        assert "Spend" in self.condition.get_upsell_message(self.offer, self.basket)

    def test_matching_basket_fails_partial_condition(self):
        add_product(self.basket, D("5"), 2)
        assert self.condition.is_partially_satisfied(self.offer, self.basket) is False

    def test_less_value_basket_passes_partial_condition(self):
        add_product(self.basket, D("5"), 1)
        assert self.condition.is_partially_satisfied(self.offer, self.basket)

    def test_matching_basket_passes_condition(self):
        add_product(self.basket, D("5"), 2)
        assert self.condition.is_satisfied(self.offer, self.basket)

    def test_greater_than_basket_passes_condition(self):
        add_product(self.basket, D("5"), 3)
        assert self.condition.is_satisfied(self.offer, self.basket)

    def test_consumption(self):
        add_product(self.basket, D("5"), 3)
        self.condition.consume_items(self.offer, self.basket, [])
        assert 1 == self.basket.all_lines()[0].quantity_without_discount

    def test_consumption_with_high_value_product(self):
        add_product(self.basket, D("15"), 1)
        self.condition.consume_items(self.offer, self.basket, [])
        assert 0 == self.basket.all_lines()[0].quantity_without_discount

    def test_is_consumed_respects_quantity_consumed(self):
        add_product(self.basket, D("15"), 1)
        assert self.condition.is_satisfied(self.offer, self.basket)
        self.condition.consume_items(self.offer, self.basket, [])
        assert self.condition.is_satisfied(self.offer, self.basket) is False


@pytest.mark.django_db
class TestCoverageCondition:
    @pytest.fixture(autouse=True)
    def setUp(self, range_some, products_some, empty_basket, coverage_condition):
        self.products = products_some
        self.range = range_some
        self.basket = empty_basket
        self.condition = coverage_condition
        self.offer = mock.Mock()

    def test_empty_basket_fails(self):
        assert self.condition.is_satisfied(self.offer, self.basket) is False

    def test_empty_basket_fails_partial_condition(self):
        assert self.condition.is_partially_satisfied(self.offer, self.basket) is False

    def test_single_item_fails(self):
        add_product(self.basket, product=self.products[0])
        assert self.condition.is_satisfied(self.offer, self.basket) is False

    def test_not_discountable_item_fails(self):
        self.products[0].is_discountable = False
        self.products[0].save()
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        assert self.condition.is_satisfied(self.offer, self.basket) is False

    def test_single_item_passes_partial_condition(self):
        add_product(self.basket, product=self.products[0])
        assert self.condition.is_partially_satisfied(self.offer, self.basket)

    def test_upsell_message(self):
        add_product(self.basket, product=self.products[0])
        assert "Buy 1 more" in self.condition.get_upsell_message(
            self.offer, self.basket
        )

    def test_duplicate_item_fails(self):
        add_product(self.basket, quantity=2, product=self.products[0])
        assert self.condition.is_satisfied(self.offer, self.basket) is False

    def test_duplicate_item_passes_partial_condition(self):
        add_product(self.basket, quantity=2, product=self.products[0])
        assert self.condition.is_partially_satisfied(self.offer, self.basket)

    def test_covering_items_pass(self):
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        assert self.condition.is_satisfied(self.offer, self.basket)

    def test_covering_items_fail_partial_condition(self):
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        assert self.condition.is_partially_satisfied(self.offer, self.basket) is False

    def test_covering_items_are_consumed(self):
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        self.condition.consume_items(self.offer, self.basket, [])
        assert 0 == self.basket.num_items_without_discount

    def test_consumed_items_checks_affected_items(self):
        # Create new offer
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        cond = models.CoverageCondition(range=product_range, type="Coverage", value=2)

        # Get 4 distinct products in the basket
        self.products.extend([factories.create_product(), factories.create_product()])
        for product in self.products:
            add_product(self.basket, product=product)

        assert cond.is_satisfied(self.offer, self.basket)
        cond.consume_items(self.offer, self.basket, [])
        assert 2 == self.basket.num_items_without_discount

        assert cond.is_satisfied(self.offer, self.basket)
        cond.consume_items(self.offer, self.basket, [])
        assert 0 == self.basket.num_items_without_discount


@pytest.mark.django_db
class TestConditionProxyModels(object):
    def test_name_and_description(self, product_range):
        """
        Tests that the condition proxy classes all return a name and
        description. Unfortunately, the current implementations means
        a valid range and value are required.
        """
        for event_type, __ in models.Condition.TYPE_CHOICES:
            condition = models.Condition(type=event_type, range=product_range, value=5)
            assert all([condition.name, condition.description, str(condition)])

    def test_proxy(self, product_range):
        for event_type, __ in models.Condition.TYPE_CHOICES:
            condition = models.Condition(type=event_type, range=product_range, value=5)
            proxy = condition.proxy()
            assert condition.type == proxy.type
            assert condition.range == proxy.range
            assert condition.value == proxy.value


class TestCustomCondition(TestCase):
    def setUp(self):
        self.condition = custom.create_condition(BasketOwnerCalledBarry)
        self.offer = models.ConditionalOffer(condition=self.condition)
        self.basket = Basket()

    def test_is_not_satisfied_by_non_match(self):
        self.basket.owner = factories.UserFactory(first_name="Alan")
        assert self.offer.is_condition_satisfied(self.basket) is False

    def test_is_satisfied_by_match(self):
        self.basket.owner = factories.UserFactory(first_name="Barry")
        assert self.offer.is_condition_satisfied(self.basket)


class TestOffersWithCountCondition(TestCase):
    def setUp(self):
        super().setUp()

        self.basket = factories.create_basket(empty=True)

        # Create range and add one product to it.
        rng = factories.RangeFactory(name="All products", includes_all_products=True)
        self.product = factories.ProductFactory()
        rng.add_product(self.product)

        # Create a non-exclusive offer #1.
        condition1 = factories.ConditionFactory(range=rng, value=D("1"))
        benefit1 = factories.BenefitFactory(range=rng, value=D("10"))
        self.offer1 = factories.ConditionalOfferFactory(
            condition=condition1,
            benefit=benefit1,
            start_datetime=now(),
            name="Test offer #1",
            exclusive=False,
        )

        # Create a non-exclusive offer #2.
        condition2 = factories.ConditionFactory(range=rng, value=D("1"))
        benefit2 = factories.BenefitFactory(range=rng, value=D("5"))
        self.offer2 = factories.ConditionalOfferFactory(
            condition=condition2,
            benefit=benefit2,
            start_datetime=now(),
            name="Test offer #2",
            exclusive=False,
        )

    def add_product(self):
        self.basket.add_product(self.product)
        self.basket.strategy = Selector().strategy()
        applicator.Applicator().apply(self.basket)

    def assertOffersApplied(self, offers):
        applied_offers = self.basket.applied_offers()
        self.assertEqual(len(offers), len(applied_offers))
        for offer in offers:
            self.assertIn(offer.id, applied_offers, msg=offer)

    def test_both_non_exclusive_offers_are_applied(self):
        self.add_product()
        self.assertOffersApplied([self.offer1, self.offer2])
