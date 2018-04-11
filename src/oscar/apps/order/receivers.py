from django.conf import settings
from django.dispatch import receiver

from .signals import order_placed
from .utils import create_invoice


@receiver(order_placed)
def receive_order_placed(sender, order, **kwargs):
    if settings.OSCAR_INVOICE_GENERATE_AFTER_ORDER_PLACED:
        create_invoice(order)
