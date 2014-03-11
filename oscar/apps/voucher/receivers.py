from oscar.apps.basket import signals


def track_voucher_addition(basket, voucher, **kwargs):
    voucher.num_basket_additions += 1
    voucher.save()


def track_voucher_removal(basket, voucher, **kwargs):
    voucher.num_basket_additions -= 1
    voucher.save()


signals.voucher_addition.connect(track_voucher_addition)
signals.voucher_removal.connect(track_voucher_removal)
