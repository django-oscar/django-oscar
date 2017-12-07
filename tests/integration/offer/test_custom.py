from django.test import TestCase

from oscar.apps.offer import custom

from tests._site.model_tests_app.models import CustomBenefitWithoutName, CustomConditionWithoutName


class TestCustomBenefit(TestCase):
    def setUp(self):
        self.custom_benefit = custom.create_benefit(CustomBenefitWithoutName)

    def test_benefit_raises_assert_on_missing_title(self):
        with self.assertRaisesMessage(AssertionError, 'Name property is not defined on proxy class.'):
            str(self.custom_benefit)


class TestCustomCondition(TestCase):
    def setUp(self):
        self.custom_condition = custom.create_condition(CustomConditionWithoutName)

    def test_benefit_raises_assert_on_missing_title(self):
        with self.assertRaisesMessage(AssertionError, 'Name property is not defined on proxy class.'):
            str(self.custom_condition)
