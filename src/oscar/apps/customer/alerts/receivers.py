from django.conf import settings
from django.db.models.signals import post_save

from oscar.core.loading import get_class, get_model

AlertsDispatcher = get_class('customer.alerts.utils', 'AlertsDispatcher')


def send_product_alerts(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    AlertsDispatcher().send_product_alert_email_for_user(instance.product)


if settings.OSCAR_EAGER_ALERTS:
    StockRecord = get_model('partner', 'StockRecord')
    post_save.connect(send_product_alerts, sender=StockRecord)
