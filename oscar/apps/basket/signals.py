import django.dispatch

basket_addition = django.dispatch.Signal(
    providing_args=["product", "user", "request"])
voucher_addition = django.dispatch.Signal(
    providing_args=["basket", "voucher"])
voucher_removal = django.dispatch.Signal(
    providing_args=["basket", "voucher"])
