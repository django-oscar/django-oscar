from django.db.models.signals import post_delete
from django.dispatch import receiver

from oscar.core.loading import get_model

ConditionalOffer = get_model("offer", "ConditionalOffer")
Condition = get_model("offer", "Condition")
Benefit = get_model("offer", "Benefit")


@receiver(post_delete, sender=ConditionalOffer)
def delete_unused_related_conditions_and_benefits(instance, **kwargs):
    offer = instance  # the object is no longer in the database

    try:
        condition = Condition.objects.get(id=offer.condition_id)
    except Condition.DoesNotExist:
        pass
    else:
        # Only delete if not using a proxy, and not used by other offers
        if condition.proxy_class == "" and not condition.offers.exists():
            condition.delete()

    try:
        benefit = Benefit.objects.get(id=offer.benefit_id)
    except Benefit.DoesNotExist:
        pass
    else:
        # Only delete if not using a proxy, and not used by other offers
        if benefit.proxy_class == "" and not benefit.offers.exists():
            benefit.delete()
