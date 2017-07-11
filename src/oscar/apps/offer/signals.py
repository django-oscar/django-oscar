from django.db.models.signals import post_delete
from django.dispatch import receiver

from oscar.core.loading import get_model

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')


@receiver(post_delete, sender=ConditionalOffer)
def delete_unused_related_conditions_and_benefits(instance, **kwargs):
    offer = instance  # the object is no longer in the database

    condition_id = offer.condition_id
    condition = Condition.objects.get(id=condition_id)
    condition_is_unique = condition.offers.count() == 0
    condition_is_not_custom = condition.proxy_class == ''
    if condition_is_not_custom and condition_is_unique:
        condition.delete()

    benefit_id = offer.benefit_id
    benefit = Benefit.objects.get(id=benefit_id)
    benefit_is_unique = benefit.offers.count() == 0
    benefit_is_not_custom = benefit.proxy_class == ''
    if benefit_is_not_custom and benefit_is_unique:
        benefit.delete()
