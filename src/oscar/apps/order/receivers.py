# coding=utf-8
from django.dispatch import receiver

from .signals import order_status_changed


@receiver(order_status_changed)
def receive_order_status_change(sender, order, old_status, new_status, **kwargs):
    order.status_changes.create(old_status=old_status, new_status=new_status)
