from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from oscar.apps.catalogue.models import Product


class AbstractNotification(models.Model):
    """
    Model of a user's notification subscriptions for products. The 
    user can be an anonymous user.
    """
    user = models.ForeignKey(User, db_index=True, blank=True, null=True,
                             related_name="notifications")
    email = models.EmailField(db_index=True, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    confirm_key = models.CharField(max_length=16, null=True)
    unsubscribe_key = models.CharField(max_length=16, null=True)

    #TODO: check what this is actually for, I don't understand it
    # used for an authenticated user to keep persistence with his notifications
    #persistence_key = models.CharField(max_length=32, null=True)

    def get_notification_email(self):
        if self.user:
            return self.user.email
        return self.email

    def __unicode__(self):
        return _(u'Notification for %s - %s') % (self.user, self.email)

    class Meta:
        abstract = True
        app_label = 'notification'


class ProductNotification(AbstractNotification):
    """
    A Notification might have several products attached. For the case a user
    requires more than one product
    """
    product = models.ForeignKey(Product, db_index=True)

    class Meta:
        app_label = 'notification'
