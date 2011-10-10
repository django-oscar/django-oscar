from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save

from oscar.core.loading import import_module
from oscar.apps.basket.abstract_models import AbstractBasket
import_module('voucher.models', ['Voucher'], locals())
import_module('order.models', ['OrderDiscount'], locals())

@receiver(m2m_changed)
def receive_basket_voucher_change(sender, **kwargs):
    if (kwargs['model'] == Voucher and kwargs['action'] == 'post_add' and
        isinstance(kwargs['instance'], AbstractBasket) and kwargs['pk_set']):
        voucher_id = list(kwargs['pk_set'])[0]
        voucher = Voucher._default_manager.get(pk=voucher_id)
        voucher.num_basket_additions += 1
        voucher.save()

@receiver(post_save, sender=OrderDiscount)        
def receive_order_discount_save(sender, instance, **kwargs):
    # Record the amount of discount against the appropriate offers
    # and vouchers
    discount = instance
    if discount.voucher:
        discount.voucher.total_discount += discount.amount
        discount.voucher.save()
    discount.offer.total_discount += discount.amount
    discount.offer.save()
    
    
        
    
