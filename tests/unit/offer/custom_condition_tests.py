from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import custom, models
from oscar.apps.basket.models import Basket
from oscar.core.compat import get_user_model


User = get_user_model()


class BasketOwnerCalledBarry(models.Condition):

    class Meta:
        proxy = True

    def is_satisfied(self, offer, basket):
        if not basket.owner:
            return False
        return basket.owner.first_name.lower() == 'barry'

    def can_apply_condition(self, product):
        return False


class TestCustomCondition(TestCase):

    def setUp(self):
        self.condition = custom.create_condition(BasketOwnerCalledBarry)
        self.offer = models.ConditionalOffer(
            condition=self.condition)
        self.basket = Basket()

    def test_is_not_satified_by_non_match(self):
        self.basket.owner = G(User, first_name="Alan")
        self.assertFalse(self.offer.is_condition_satisfied(self.basket))

    def test_is_satified_by_match(self):
        self.basket.owner = G(User, first_name="Barry")
        self.assertTrue(self.offer.is_condition_satisfied(self.basket))
