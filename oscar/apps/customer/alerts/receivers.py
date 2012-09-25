from django.conf import settings
from django.db.models import get_model
from django.db.models.signals import post_save
from django.contrib.auth.models import User


def send_product_alerts(sender, instance, created, **kwargs):
    from oscar.apps.customer.alerts import utils
    utils.send_product_alerts(instance.product)


def migrate_alerts_to_user(sender, instance, created, **kwargs):
    """
    Transfer any active alerts linked to a user's email address to the newly
    registered user.
    """
    if created:
        ProductAlert = get_model('customer', 'ProductAlert')
        alerts = ProductAlert.objects.filter(email=instance.email, status=ProductAlert.ACTIVE)
        alerts.update(user=instance, key=None, email=None)


post_save.connect(migrate_alerts_to_user, sender=User)


if settings.OSCAR_EAGER_ALERTS:
    StockRecord = get_model('partner', 'StockRecord')
    post_save.connect(send_product_alerts, sender=StockRecord)
