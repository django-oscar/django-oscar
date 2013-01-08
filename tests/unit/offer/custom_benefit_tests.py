from decimal import Decimal as D

from django.test import TestCase
from django.contrib.auth.models import User
from django_dynamic_fixture import G
import mock

from oscar.apps.offer import custom, models
from oscar.apps.basket.models import Basket


class ChangesOwnerName(models.Benefit):

    class Meta:
        proxy = True

    def apply(self, basket, condition, offer=None):
        basket.owner.first_name = "Terry"
        basket.owner.save()
        return D('0.00')

    @property
    def description(self):
        return 'Changes owners name'


class NoDescription(models.Benefit):

    class Meta:
        proxy = True

    def apply(self, basket, condition, offer=None):
        return D('0.00')


class TestACustomBenefit(TestCase):

    def test_must_implement_a_description_property(self):
        with self.assertRaises(RuntimeError):
            custom.create_benefit(NoDescription)


class TestCustomBenefit(TestCase):

    def setUp(self):
        self.benefit = custom.create_benefit(ChangesOwnerName)
        self.condition = mock.Mock()
        self.basket = Basket()

    def test_applies_correctly(self):
        self.basket.owner = G(User, first_name="Alan")
        self.benefit.proxy().apply(self.basket, self.condition)
        self.assertEqual("Terry", self.basket.owner.first_name)
