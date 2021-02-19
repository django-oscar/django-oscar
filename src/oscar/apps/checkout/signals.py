from django.dispatch import Signal

start_checkout = Signal()
pre_payment = Signal()
post_payment = Signal()
post_checkout = Signal()
