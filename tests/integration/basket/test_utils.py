
import pytest
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


@pytest.mark.django_db
class TestLineOfferConsumer(object):

    def test_consumed_no_offer(self, filled_basket):
        for line in filled_basket.all_lines():
            assert line.consumer.consumed() == 0

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

    def test_consumed_with_exclusive_offer(self, filled_basket):
        offer1 = ConditionalOfferFactory(name='offer1')
        offer2 = ConditionalOfferFactory(name='offer2')
        offer3 = ConditionalOfferFactory(name='offer3')
        offer1.exclusive = True
        offer2.exclusive = False
        offer3.exclusive = False

        for line in filled_basket.all_lines():
            assert line.consumer.consumed(offer1) == 0
            assert line.consumer.consumed(offer2) == 0

        line1 = filled_basket.all_lines()[0]
        line2 = filled_basket.all_lines()[1]

        line1.consumer.consume(1, offer1)
        assert line1.is_available_for_offer_discount(offer2) is True

        line1.consumer.consume(99, offer1)
        assert line1.is_available_for_offer_discount(offer2) is False

        line2.consumer.consume(1, offer2)
        assert line2.is_available_for_offer_discount(offer1) is True

        line2.consumer.consume(99, offer2)
        assert line2.is_available_for_offer_discount(offer1) is False
        assert line2.is_available_for_offer_discount(offer3) is True
