from django.db import models
from django.contrib.auth.models import User

from oscar.apps.catalogue.models import Product


class NotificationList(models.Model):
    """
    Model of a user's notification subscriptions for products. The 
    user can be an anonymous user.
    """
    active = models.BooleanField(db_index=True, default=True)
    user = models.OneToOneField(User, db_index=True, null=True,
                                related_name="notifications")
    email = models.EmailField(db_index=True)
    confirm_key = models.CharField(max_length=16, null=True)
    unsubscribe_key = models.CharField(max_length=16, null=True)

    # used for an authenticated user to keep persistence with his notifications
    persistence_key = models.CharField(max_length=32, null=True)

    def __unicode__(self):
        return u'Notifications for %s - %s' % (self.user, self.email)

    class Meta:
        app_label = 'notification'


class ProductNotification(models.Model):
    """
    A Notification might have several products attached. For the case a user
    requires more than one product
    """
    notification = models.ForeignKey(NotificationList, db_index=True)
    product = models.ForeignKey(Product, db_index=True)

    class Meta:
        app_label = 'notification'
