from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save
from django.db.models import get_model

from oscar.apps.basket.abstract_models import AbstractBasket
Voucher = get_model('voucher', 'Voucher')
OrderDiscount = get_model('order', 'OrderDiscount')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


@receiver(m2m_changed)
def receive_basket_voucher_change(sender, **kwargs):
    if (kwargs['model'] == Voucher and kwargs['action'] == 'post_add' and
        isinstance(kwargs['instance'], AbstractBasket) and kwargs['pk_set']):
        voucher_id = list(kwargs['pk_set'])[0]
        voucher = Voucher._default_manager.get(pk=voucher_id)
        voucher.num_basket_additions += 1
        voucher.save()
