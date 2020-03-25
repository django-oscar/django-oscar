from django.db.models.signals import post_delete
from django.dispatch import receiver

from oscar.apps.voucher.utils import get_offer_name
from oscar.core.loading import get_model

Voucher = get_model('voucher', 'Voucher')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


@receiver(post_delete, sender=Voucher)
def delete_unused_related_conditional_offer(instance, **kwargs):
    voucher = instance  # the object is no longer in the database

    try:
        conditional_offer = ConditionalOffer.objects.get(
            name=get_offer_name(voucher.name),
            offer_type=ConditionalOffer.VOUCHER
        )
    except (ConditionalOffer.DoesNotExist, ConditionalOffer.MultipleObjectsReturned):
        pass
    else:
        # Only delete if not used by other vouchers
        if not conditional_offer.vouchers.exists():
            conditional_offer.delete()
