import sha
import random

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


class AbstractNotification(models.Model):
    """
    Abstract class defining the basic field required for a notification.
    To create a custom notification, this class must be subclassed and
    ``get_confirm_url`` and ``get_unsubscribe`` URL have to be overwritten
    in it.
    A notification can have two different status for authenticated
    users (``ACTIVE`` and ``INACTIVE`` and anonymous users have an
    additional status ``UNCONFIRMED``. For anonymous users a confirmation
    and unsubscription key are generated when an instance is saved for
    the first time and can be used to confirm and unsubscribe the
    notifications.
    """
    KEY_LENGTH = 40
    user = models.ForeignKey(User, db_index=True, blank=True, null=True,
                             related_name="notifications")
    # These fields only apply to unauthenticated users and are empty
    # if the user is registered in the system
    email = models.EmailField(db_index=True, blank=True, null=True)
    confirm_key = models.CharField(max_length=KEY_LENGTH, null=True)
    unsubscribe_key = models.CharField(max_length=KEY_LENGTH, null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_notified = models.DateTimeField(blank=True, null=True)

    UNCONFIRMED, ACTIVE, INACTIVE = ('unconfirmed', 'active', 'inactive')
    STATUS_TYPES = (
        (UNCONFIRMED, _('Not Yet Confirmed')),
        (ACTIVE, _('Active')),
        (INACTIVE, _('Inactive')),
    )
    status = models.CharField(max_length=20, choices=STATUS_TYPES,
                              default=INACTIVE)

    def is_active(self):
        """
        Check if the notification is active or not.
        Returns ``True`` if notification is active, ``False`` otherwise.
        """
        return self.status == self.ACTIVE

    def is_confirmed(self):
        """
        Check if the notification is confirmed or not.
        Returns ``True`` if notification is confirmed, ``False`` otherwise.
        """
        return self.status != self.UNCONFIRMED

    def get_random_key(self):
        """
        Get a random generated key based on SHA-1 and the notification
        email provided in this instance of the notification.
        """
        salt = sha.new(str(random.random())).hexdigest()
        return sha.new(salt + self.get_notification_email()).hexdigest()

    def get_notification_email(self):
        """
        Get the notification email address of the user subscribed to
        this notification. Return the user's email for an authenticated
        user and the email property for an anonymous user.
        """
        if self.user:
            return self.user.email
        return self.email

    def transfer_to_user(self, user):
        """
        Convenience function that allows for assigning a notification
        to a user. This is aimed at the situation when a user has
        notifications available as anonymous user but decides to sign
        up. In this case, the notification will be transfered to the
        specific user account.
        """
        if not self.user:
            self.user = user
            self.email = None
            self.confirm_key, self.unsubscribe_key = None, None
            self.save()

    @models.permalink
    def get_confirm_url(self):
        """
        Get confirmation URL for this notification. Needs to be
        implemented in subclasses.
        """
        raise NotImplementedError()

    @models.permalink
    def get_unsubscribe_url(self):
        """
        Get confirmation URL for this notification. Needs to be
        implemented in subclasses.
        """
        raise NotImplementedError()

    def save(self, *args, **kwargs):
        """
        Save the current notification instance. If the user is not
        a registered/authenticated user, a confirmation and
        unsubscription key will be generated for the notification.
        """
        if self.email and not self.user:
            if not self.confirm_key:
                self.confirm_key = self.get_random_key()
            if not self.unsubscribe_key:
                self.unsubscribe_key = self.get_random_key()
        return super(AbstractNotification, self).save(*args, **kwargs)

    def get_notification_item(self):
        """
        Get the item of this notification for. This is an abstract
        declaration and needs to be overwritten in subclasses. The
        expected return value is either a model instance or ``None``.
        """
        raise NotImplementedError()

    def __unicode__(self):
        """ Unicode representation of this notification """
        return _(u'Notification for %(user)s - %(email)s') % {
            'user': self.user or _("anonymous"),
            'email': self.email
        }

    class Meta:
        abstract = True
        app_label = 'notification'
