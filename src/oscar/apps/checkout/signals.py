from django.dispatch import Signal

start_checkout = Signal(providing_args=["request"])
pre_payment = Signal(providing_args=["view"])
post_payment = Signal(providing_args=["view"])
post_checkout = Signal(providing_args=["order", "user", "request", "response"])
