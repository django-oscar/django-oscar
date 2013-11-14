from django.conf import settings
from django.db.models import get_model
from django.db.models.signals import post_save
from django.db import connection

from oscar.core.compat import get_user_model


User = get_user_model()


def send_product_alerts(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    from oscar.apps.customer.alerts import utils
    utils.send_product_alerts(instance.product)


def migrate_alerts_to_user(sender, instance, created, **kwargs):
    """
    Transfer any active alerts linked to a user's email address to the newly
    registered user.
    """
    if not created:
        return
    ProductAlert = get_model('customer', 'ProductAlert')

    # This signal will be raised when creating a superuser as part of syncdb,
    # at which point only a subset of tables will be created.  Thus, we test if
    # the alert table exists before trying to exercise the ORM.
    table = ProductAlert._meta.db_table
    if table in connection.introspection.table_names():
        alerts = ProductAlert.objects.filter(
            email=instance.email, status=ProductAlert.ACTIVE)
        alerts.update(user=instance, key=None, email=None)


post_save.connect(migrate_alerts_to_user, sender=User)


if settings.OSCAR_EAGER_ALERTS:
    StockRecord = get_model('partner', 'StockRecord')
    post_save.connect(send_product_alerts, sender=StockRecord)
