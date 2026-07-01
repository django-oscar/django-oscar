from django.test import TestCase

from oscar.apps.offer import custom, models
from oscar.test import factories
from tests._site.model_tests_app.models import (
    BasketOwnerCalledBarry,
    CustomBenefitModel,
)


class TestConditionalOfferDelete(TestCase):
    def test_benefits_and_conditions_deleted(self):
        offer = factories.ConditionalOfferFactory()

        benefit_id = offer.benefit.id
        condition_id = offer.condition.id

        offer.delete()

        self.assertFalse(models.Condition.objects.filter(id=condition_id).exists())
        self.assertFalse(models.Benefit.objects.filter(id=benefit_id).exists())

    def test_for_multiple_offers_benefits_and_conditions_not_deleted(self):
        condition = factories.ConditionFactory()
        condition_id = condition.id
        benefit = factories.BenefitFactory()
        benefit_id = benefit.id

        offer1 = factories.create_offer(name="First test offer", condition=condition)
        offer2 = factories.create_offer(
            name="Second test offer", condition=condition, benefit=benefit
        )
        offer3 = factories.create_offer(name="Third test offer", benefit=benefit)

        offer1.delete()
        self.assertTrue(models.Condition.objects.filter(id=condition_id).exists())

        offer2.delete()
        self.assertFalse(models.Condition.objects.filter(id=condition_id).exists())
        self.assertTrue(models.Benefit.objects.filter(id=benefit_id).exists())

        offer3.delete()
        self.assertFalse(models.Benefit.objects.filter(id=benefit_id).exists())

    def test_custom_benefits_and_conditions_not_deleted(self):
        condition = custom.create_condition(BasketOwnerCalledBarry)
        condition_id = condition.id

        benefit = custom.create_benefit(CustomBenefitModel)
        benefit_id = benefit.id

        offer = factories.create_offer(benefit=benefit, condition=condition)
        offer.delete()

        self.assertTrue(models.Condition.objects.filter(id=condition_id).exists())
        self.assertTrue(models.Benefit.objects.filter(id=benefit_id).exists())
