from django.db import models
from django.utils.translation import ugettext_lazy as _


class Notification(models.Model):
    sender = models.ForeignKey('auth.User', null=True)
    recipient = models.ForeignKey('auth.User', related_name='notifications')

    subject = models.CharField(max_length=255)
    body = models.TextField()

    # Some projects may want to categorise their notifications.  You may want
    # to use this field to show a different icons next to the notification.
    category = models.CharField(max_length=255, null=True)

    INBOX, ARCHIVE = 'Inbox', 'Archive'
    choices = (
        (INBOX, _(INBOX)),
        (ARCHIVE, _(ARCHIVE)))
    location = models.CharField(max_length=32, choices=choices,
                                default=INBOX)

    date_sent = models.DateTimeField(auto_now_add=True)
    date_read = models.DateTimeField(null=True)


class StockReminder(models.Model):
    user = models.ForeignKey('auth.User', related_name='stock_reminders')
    # + other fields so anonymous users can get reminders too
    product = models.ForeignKey('catalogue.Product')
    UNCONFIRMED, ACTIVE, INACTIVE = ('unconfirmed', 'active', 'inactive')
    STATUS_TYPES = (
        (UNCONFIRMED, _('Not yet confirmed')),
        (ACTIVE, _('Active')),
        (INACTIVE, _('Inactive')),
    )
    status = models.CharField(max_length=20, choices=STATUS_TYPES,
                              default=INACTIVE)

    date_created = models.DateTimeField(auto_now_add=True)
    date_notified = models.DateTimeField(null=True)
