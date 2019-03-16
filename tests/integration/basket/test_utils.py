
import pytest

from oscar.apps.offer import models
from oscar.apps.offer.applicator import Applicator
from oscar.test.factories import (
    BasketFactory, ConditionalOfferFactory, ProductFactory)


@pytest.fixture
def filled_basket():
    basket = BasketFactory()
    product1 = ProductFactory()
    product2 = ProductFactory()
    basket.add_product(product1, quantity=10)
    basket.add_product(product2, quantity=20)
    return basket


@pytest.fixture
def single_offer():
    return ConditionalOfferFactory(
        condition__range__includes_all_products=True,
        condition__value=1,
        benefit__range__includes_all_products=True,
        benefit__max_affected_items=1,
        name='offer1',
        exclusive=False,
    )


@pytest.fixture
def multi_offers():
    offer1 = ConditionalOfferFactory(
        condition__range__includes_all_products=True,
        benefit__range__includes_all_products=True,
        name='offer1',
        exclusive=False,
    )
    offer2 = ConditionalOfferFactory(
        condition__range__includes_all_products=True,
        benefit__range__includes_all_products=True,
        name='offer2',
        exclusive=False
    )
    offer3 = ConditionalOfferFactory(
        condition__range__includes_all_products=True,
        benefit__range__includes_all_products=True,
        name='offer3',
        exclusive=False
    )
    return offer1, offer2, offer3


@pytest.mark.django_db
class TestLineOfferConsumer:

    def test_consumed_no_offer(self, filled_basket):
        for line in filled_basket.all_lines():
            assert line.consumer.consumed() == 0

    def test_available_with_offer(self):
        basket = BasketFactory()
        product1 = ProductFactory()
        product2 = ProductFactory()
        basket.add_product(product1, quantity=1)
        basket.add_product(product2, quantity=10)

        benefit = models.Benefit(
            type=models.Benefit.PERCENTAGE,
            value=10,
            max_affected_items=5,
        )
        benefit.save()

        offer1 = ConditionalOfferFactory(name='offer1', benefit=benefit)
        lines = basket.all_lines()
        assert lines[0].consumer.available(offer1) == 1
        assert lines[1].consumer.available(offer1) == 5

    def test_consumed_with_offer(self, filled_basket):
        offer1 = ConditionalOfferFactory(name='offer1')
        offer2 = ConditionalOfferFactory(name='offer2')
        offer1.exclusive = False
        offer2.exclusive = False

        for line in filled_basket.all_lines():
            assert line.consumer.consumed(offer1) == 0
            assert line.consumer.consumed(offer2) == 0

        line1 = filled_basket.all_lines()[0]
        line2 = filled_basket.all_lines()[1]

        line1.consumer.consume(1, offer1)
        assert line1.consumer.consumed() == 1
        assert line1.consumer.consumed(offer1) == 1
        assert line1.consumer.consumed(offer2) == 0

        line1.consumer.consume(9, offer1)
        assert line1.consumer.consumed() == line1.quantity
        assert line1.consumer.consumed(offer1) == line1.quantity
        assert line1.consumer.consumed(offer2) == 0

        line1.consumer.consume(99, offer1)
        assert line1.consumer.consumed(offer1) == line1.quantity
        assert line1.consumer.consumed(offer2) == 0

        line1.consumer.consume(1, offer2)
        line2.consumer.consume(1, offer2)

        assert line1.consumer.consumed(offer2) == 1
        assert line2.consumer.consumed(offer2) == 1

    def test_consume(self, filled_basket):
        line = filled_basket.all_lines()[0]
        line.consume(1)
        assert line.quantity_with_discount == 1
        line.consume(99)
        assert line.quantity_with_discount == 10

    def test_consumed_with_exclusive_offer_1(self, filled_basket):
        offer1 = ConditionalOfferFactory(name='offer1')
        offer2 = ConditionalOfferFactory(name='offer2')
        offer3 = ConditionalOfferFactory(name='offer3')
        offer1.exclusive = True
        offer2.exclusive = False
        offer3.exclusive = False

        for line in filled_basket.all_lines():
            assert line.consumer.consumed(offer1) == 0
            assert line.consumer.consumed(offer2) == 0

        line1, line2 = list(filled_basket.all_lines())

        # exclusive offer consumes one item on line1
        line1.consumer.consume(1, offer1)

        # offer1 is exclusive so that blocks other offers
        assert line1.is_available_for_offer_discount(offer2) is False

        line1.consumer.consume(99, offer1)
        # ran out of room for offer1
        assert line1.is_available_for_offer_discount(offer1) is False
        # offer2 was never an option
        assert line1.is_available_for_offer_discount(offer2) is False

        # exclusivity is per line so line2 is available for offer2
        line2.consumer.consume(1, offer2)
        # nope: exclusive and non-exclusive don't mix
        assert line2.is_available_for_offer_discount(offer1) is False

        line2.consumer.consume(99, offer2)
        # ran out of room for offer2
        assert line2.is_available_for_offer_discount(offer1) is False
        # but still room for offer3!
        assert line2.is_available_for_offer_discount(offer3) is True

    def test_consumed_with_exclusive_offer_2(self, filled_basket):
        offer1 = ConditionalOfferFactory(name='offer1')
        offer2 = ConditionalOfferFactory(name='offer2')
        offer3 = ConditionalOfferFactory(name='offer3')
        offer1.exclusive = True
        offer2.exclusive = False
        offer3.exclusive = False

        for line in filled_basket.all_lines():
            assert line.consumer.consumed(offer1) == 0
            assert line.consumer.consumed(offer2) == 0

        line1, line2 = list(filled_basket.all_lines())

        # exclusive offer consumes one item on line1
        line1.consumer.consume(1, offer1)
        remaining1 = line1.quantity - 1

        assert line1.quantity_with_offer_discount(offer1) == 1
        assert line1.quantity_with_offer_discount(offer2) == 0
        assert line1.quantity_with_offer_discount(offer3) == 0

        assert line1.quantity_without_offer_discount(offer1) == remaining1
        assert line1.quantity_without_offer_discount(offer2) == 0
        assert line1.quantity_without_offer_discount(offer3) == 0

        # exclusive offer consumes all items on line1
        line1.consumer.consume(remaining1, offer1)
        assert line1.quantity_with_offer_discount(offer1) == line1.quantity
        assert line1.quantity_with_offer_discount(offer2) == 0
        assert line1.quantity_with_offer_discount(offer3) == 0

        assert line1.quantity_without_offer_discount(offer1) == 0
        assert line1.quantity_without_offer_discount(offer2) == 0
        assert line1.quantity_without_offer_discount(offer3) == 0

        # non-exclusive offer consumes one item on line2
        line2.consumer.consume(1, offer2)
        remaining2 = line2.quantity - 1

        assert line2.quantity_with_offer_discount(offer1) == 0
        assert line2.quantity_with_offer_discount(offer2) == 1
        assert line2.quantity_with_offer_discount(offer3) == 0

        assert line2.quantity_without_offer_discount(offer1) == 0
        assert line2.quantity_without_offer_discount(offer2) == remaining2
        assert line2.quantity_without_offer_discount(offer3) == line2.quantity

        # non-exclusive offer consumes all items on line2
        line2.consumer.consume(remaining2, offer2)

        assert line2.quantity_with_offer_discount(offer1) == 0
        assert line2.quantity_with_offer_discount(offer2) == line2.quantity
        assert line2.quantity_with_offer_discount(offer3) == 0

        assert line2.quantity_without_offer_discount(offer1) == 0
        assert line2.quantity_without_offer_discount(offer2) == 0
        assert line2.quantity_without_offer_discount(offer3) == line2.quantity

    def test_consumed_by_application(self, filled_basket, single_offer):
        basket = filled_basket
        Applicator().apply(basket)
        assert len(basket.offer_applications.offer_discounts) == 1
        assert [x.consumer.consumed() for x in basket.all_lines()] == [1, 0]

    def test_consumed_with_combined_offer(self, filled_basket):
        offer1 = ConditionalOfferFactory(name='offer1')
        offer2 = ConditionalOfferFactory(name='offer2')
        offer3 = ConditionalOfferFactory(name='offer3')
        offer4 = ConditionalOfferFactory(name='offer4')
        offer1.exclusive = True
        offer2.exclusive = False
        offer3.exclusive = False
        offer4.exclusive = False
        offer2.combinations.add(offer3)
        assert offer3 in offer2.combined_offers
        assert offer2 in offer3.combined_offers

        for line in filled_basket.all_lines():
            assert line.consumer.consumed(offer1) == 0
            assert line.consumer.consumed(offer2) == 0
            assert line.consumer.consumed(offer3) == 0

        line1 = filled_basket.all_lines()[0]

        # combinable offer consumes one item of line1
        line1.consumer.consume(1, offer2)
        remaining1 = line1.quantity - 1

        assert line1.quantity_with_offer_discount(offer1) == 0
        assert line1.quantity_with_offer_discount(offer2) == 1
        assert line1.quantity_with_offer_discount(offer3) == 0
        assert line1.quantity_with_offer_discount(offer4) == 0

        assert line1.quantity_without_offer_discount(offer1) == 0
        assert line1.quantity_without_offer_discount(offer2) == remaining1
        assert line1.quantity_without_offer_discount(offer3) == line1.quantity
        assert line1.quantity_without_offer_discount(offer4) == 0

        # combinable offer consumes one item of line1
        line1.consumer.consume(1, offer3)
        assert line1.quantity_with_offer_discount(offer1) == 0
        assert line1.quantity_with_offer_discount(offer2) == 1
        assert line1.quantity_with_offer_discount(offer3) == 1
        assert line1.quantity_with_offer_discount(offer4) == 0

        assert line1.quantity_without_offer_discount(offer1) == 0
        assert line1.quantity_without_offer_discount(offer2) == remaining1
        assert line1.quantity_without_offer_discount(offer3) == remaining1
        assert line1.quantity_without_offer_discount(offer4) == 0

        # combinable offer consumes all items of line1
        line1.consumer.consume(remaining1, offer2)

        assert line1.quantity_with_offer_discount(offer1) == 0
        assert line1.quantity_with_offer_discount(offer2) == line1.quantity
        assert line1.quantity_with_offer_discount(offer3) == 1
        assert line1.quantity_with_offer_discount(offer4) == 0

        assert line1.quantity_without_offer_discount(offer1) == 0
        assert line1.quantity_without_offer_discount(offer2) == 0
        assert line1.quantity_without_offer_discount(offer3) == remaining1
        assert line1.quantity_without_offer_discount(offer4) == 0
