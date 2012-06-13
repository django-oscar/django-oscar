from django.dispatch import Signal

pre_payment = Signal(providing_args=["view"])
post_payment = Signal(providing_args=["view"])