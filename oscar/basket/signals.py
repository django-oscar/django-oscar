import django.dispatch

basket_addition = django.dispatch.Signal(providing_args=["product", "user"])
basket_voucher = django.dispatch.Signal(providing_args=["basket", "voucher"])