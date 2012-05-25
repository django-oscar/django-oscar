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
    # these field only apply to unauthenticated users and are empty
    # if the user is registered in the system
    email = models.EmailField(db_index=True, blank=True, null=True)
    confirm_key = models.CharField(max_length=16, null=True)
    unsubscribe_key = models.CharField(max_length=16, null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    UNCONFIRMED, ACTIVE, INACTIVE = ('unconfirmed', 'active', 'inactive')
    STATUS_TYPES = (
        (UNCONFIRMED, _('Not Yet Confirmed')),
        (ACTIVE, _('Active')),
        (INACTIVE, _('Inactive')),
    )
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default=INACTIVE)

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
