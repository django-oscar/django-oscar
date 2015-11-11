from django.test import TestCase
from django.utils import six

from oscar.apps.offer import custom, models
from oscar.apps.basket.models import Basket
from oscar.test import factories


class TestConditionProxyModels(TestCase):

    def test_name_and_description(self):
        """
        Tests that the condition proxy classes all return a name and
        description. Unfortunately, the current implementations means
        a valid range and value are required.
        This test became necessary because the complex name/description logic
        broke with the python_2_unicode_compatible decorator.
        """
        range = factories.RangeFactory()
        for type, __ in models.Condition.TYPE_CHOICES:
            condition = models.Condition(type=type, range=range, value=5)
            self.assertTrue(all([
                condition.name,
                condition.description,
                six.text_type(condition)]))


class BasketOwnerCalledBarry(models.Condition):

    class Meta:
        proxy = True
        app_label = 'tests'

    def is_satisfied(self, offer, basket):
        if not basket.owner:
            return False
        return basket.owner.first_name.lower() == 'barry'

    def can_apply_condition(self, product):
        return False


class TestCustomCondition(TestCase):

    def setUp(self):
        self.condition = custom.create_condition(BasketOwnerCalledBarry)
        self.offer = models.ConditionalOffer(condition=self.condition)
        self.basket = Basket()

    def test_is_not_satified_by_non_match(self):
        self.basket.owner = factories.UserFactory(first_name="Alan")
        self.assertFalse(self.offer.is_condition_satisfied(self.basket))

    def test_is_satified_by_match(self):
        self.basket.owner = factories.UserFactory(first_name="Barry")
        self.assertTrue(self.offer.is_condition_satisfied(self.basket))

