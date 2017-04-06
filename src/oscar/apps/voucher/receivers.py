from django.db.models import F

from oscar.core.loading import get_classes

voucher_addition, voucher_removal = get_classes(
    'basket.signals', ('voucher_addition', 'voucher_removal'))


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


voucher_addition.connect(track_voucher_addition)
voucher_removal.connect(track_voucher_removal)
