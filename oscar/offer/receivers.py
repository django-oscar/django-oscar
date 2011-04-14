from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save

from oscar.services import import_module
offer_models = import_module('offer.models', ['Voucher'])
order_models = import_module('order.models', ['OrderDiscount'])

@receiver(m2m_changed)
def receive_basket_voucher_change(sender, **kwargs):
    if kwargs['model'] == offer_models.Voucher and kwargs['action'] == 'post_add':
        voucher_id = list(kwargs['pk_set'])[0]
        voucher = offer_models.Voucher._default_manager.get(pk=voucher_id)
        voucher.num_basket_additions += 1
        voucher.save()

@receiver(post_save, sender=order_models.OrderDiscount)        
def receive_order_discount_save(sender, instance, **kwargs):
    # Record the amount of discount against the appropriate offers
    # and vouchers
    discount = instance
    if discount.voucher:
        discount.voucher.total_discount += discount.amount
        discount.voucher.save()
    discount.offer.total_discount += discount.amount
    discount.offer.save()
    
    
        
    
