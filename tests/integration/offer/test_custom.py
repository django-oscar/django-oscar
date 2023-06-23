from django.test import TestCase

from oscar.apps.offer import custom
from tests._site.model_tests_app.models import (
    CustomBenefitModel,
    CustomBenefitWithoutName,
    CustomConditionModel,
    CustomConditionWithoutName,
)


class TestCustomBenefit(TestCase):
    def setUp(self):
        self.custom_benefits = [
            custom.create_benefit(CustomBenefitModel),
            custom.create_benefit(CustomBenefitWithoutName),
        ]

    def test_name(self):
        self.assertEqual(self.custom_benefits[0].name, "Test benefit")

    def test_raises_assert_on_missing_name(self):
        with self.assertRaisesMessage(
            AssertionError, "Name property is not defined on proxy class."
        ):
            str(self.custom_benefits[1])


class TestCustomCondition(TestCase):
    def setUp(self):
        self.custom_conditions = [
            custom.create_condition(CustomConditionModel),
            custom.create_condition(CustomConditionWithoutName),
        ]

    def test_name(self):
        self.assertEqual(self.custom_conditions[0].name, "Test condition")

    def test_raises_assert_on_missing_name(self):
        with self.assertRaisesMessage(
            AssertionError, "Name property is not defined on proxy class."
        ):
            str(self.custom_conditions[1])
