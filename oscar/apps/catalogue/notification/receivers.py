from django.conf import settings

from oscar.core.loading import get_class
from oscar.apps.catalogue.notification import utils

# use get_class instead of get_model as this module get imported
# in the models module of notification. That means models are not
# available at this point in time.
StockRecord = get_class('partner.models', 'StockRecord')


def send_email_notifications(sender, instance, created, **kwargs):
    """
    Check for notifications for this product and send email to users
    if the product is back in stock. Add a little 'hurry' note if the
    amount of in-stock items is less then the number of notifications.
    """
    utils.send_email_notifications_for_product(instance.product)


if settings.OSCAR_INSTANT_NOTIFICATION_ENABLED:
    from django.db.models.signals import post_save
    post_save.connect(send_email_notifications, sender=StockRecord)
