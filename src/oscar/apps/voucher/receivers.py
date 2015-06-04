from django.db.models import F

from oscar.apps.basket import signals


def track_voucher_addition(basket, voucher, **kwargs):
    voucher.num_basket_additions += 1
    voucher.__class__._default_manager.filter(pk=voucher.pk).update(
        num_basket_additions=F('num_basket_additions') + 1,
    )


def track_voucher_removal(basket, voucher, **kwargs):
    voucher.num_basket_additions -= 1
    voucher.__class__._default_manager.filter(pk=voucher.pk).update(
        num_basket_additions=F('num_basket_additions') - 1,
    )


signals.voucher_addition.connect(track_voucher_addition)
signals.voucher_removal.connect(track_voucher_removal)
