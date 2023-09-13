from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models, utils
from oscar.apps.shipping.models import WeightBased
from oscar.apps.shipping.repository import Repository
from oscar.test import factories
from oscar.test.basket import add_product


def create_offer():
    product_range = models.Range.objects.create(
        name="All products", includes_all_products=True
    )
    condition = models.CountCondition.objects.create(
        range=product_range, type=models.Condition.COUNT, value=1
    )
    benefit = models.ShippingFixedPriceBenefit.objects.create(
        type=models.Benefit.SHIPPING_FIXED_PRICE, value=D("1.00")
    )
    return models.ConditionalOffer.objects.create(
        condition=condition, benefit=benefit, offer_type=models.ConditionalOffer.SITE
    )


class TestWeightBasedShippingBenefit(TestCase):
    def setUp(self):
        product = factories.create_product(attributes={"weight": 5}, num_in_stock=10)
        factories.create_shipping_weight_band(10, 10)
        self.basket = factories.create_basket(empty=True)
        self.basket.add_product(product)
        self.offer = create_offer()

    def test_has_discount_recorded_correctly_when_order_is_placed(self):
        add_product(self.basket, D("12.00"), 1)
        utils.Applicator().apply(self.basket)
        self.assertEqual(1, len(self.basket.offer_applications))

        shipping_method = WeightBased.objects.first()
        shipping_method = Repository().apply_shipping_offer(
            self.basket, shipping_method, self.offer
        )
        order = factories.create_order(
            basket=self.basket, shipping_method=shipping_method
        )

        discounts = order.discounts.all()
        self.assertEqual(1, len(discounts))

        discount = discounts[0]
        self.assertTrue(discount.is_shipping_discount)
        self.assertEqual(D("9.00"), discount.amount)
