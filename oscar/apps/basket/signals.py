import django.dispatch

basket_addition = django.dispatch.Signal(providing_args=["product", "user"])
voucher_addition = django.dispatch.Signal(providing_args=["basket", "voucher"])
