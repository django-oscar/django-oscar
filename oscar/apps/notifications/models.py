from django.db import models
from django.utils.translation import ugettext_lazy as _


class Notification(models.Model):
    recipient = models.ForeignKey('auth.User', related_name='notifications',
                                  db_index=True)

    # Not all notifications will have a sender.
    sender = models.ForeignKey('auth.User', null=True)

    # HTML is allowed in this field as it can contain links
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

    class Meta:
        ordering = ('-date_sent',)

    def __unicode__(self):
        return self.subject

    def archive(self):
        self.location = self.ARCHIVE
        self.save()
