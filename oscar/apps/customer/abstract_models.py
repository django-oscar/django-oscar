from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context, TemplateDoesNotExist
from django.template.loader import get_template
from django.conf import settings

from oscar.apps.customer.managers import CommunicationTypeManager


class AbstractEmail(models.Model):
    """
    This is a record of all emails sent to a customer.
    Normally, we only record order-related emails.
    """
    user = models.ForeignKey('auth.User', related_name='emails', verbose_name=_("User"))
    subject = models.TextField(_('Subject'), max_length=255)
    body_text = models.TextField(_("Body Text"))
    body_html = models.TextField(_("Body HTML"), blank=True, null=True)
    date_sent = models.DateTimeField(_("Date Sent"), auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _('Email')
        verbose_name_plural = _('Emails')

    def __unicode__(self):
        return _("Email to %(user)s with subject '%(subject)s'") % {
            'user': self.user.username, 'subject': self.subject}


class AbstractCommunicationEventType(models.Model):

    # Code used for looking up this event programmatically.
    # eg. PASSWORD_RESET
    code = models.SlugField(_('Code'), max_length=128)

    # Name is the friendly description of an event for use in the admin
    name = models.CharField(_('Name'), max_length=255)

    # We allow communication types to be categorised
    ORDER_RELATED = _('Order related')
    USER_RELATED = _('User related')
    category = models.CharField(_('Category'), max_length=255, default=ORDER_RELATED)

    # Template content for emails
    email_subject_template = models.CharField(_('Email Subject Template'), max_length=255, blank=True)
    email_body_template = models.TextField(_('Email Body Template'), blank=True, null=True)
    email_body_html_template = models.TextField(_('Email Body HTML Temlate'), blank=True, null=True,
        help_text=_("HTML template"))

    # Template content for SMS messages
    sms_template = models.CharField(_('SMS Template'), max_length=170, blank=True, help_text=_("SMS template"))

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True)

    objects = CommunicationTypeManager()

    # File templates
    email_subject_template_file = 'customer/emails/commtype_%s_subject.txt'
    email_body_template_file = 'customer/emails/commtype_%s_body.txt'
    email_body_html_template_file = 'customer/emails/commtype_%s_body.html'
    sms_template_file = 'customer/sms/commtype_%s_body.txt'

    class Meta:
        abstract = True
        verbose_name = _("Communication Event Type")
        verbose_name_plural = _("Communication Event Types")

    def get_messages(self, ctx=None):
        """
        Return a dict of templates with the context merged in

        We look first at the field templates but fail over to
        a set of file templates that follow a conventional path.
        """
        code = self.code.lower()

        # Build a dict of message name to Template instance
        templates = {'subject': 'email_subject_template',
                     'body': 'email_body_template',
                     'html': 'email_body_html_template',
                     'sms': 'sms_template'}
        for name, attr_name in templates.items():
            field = getattr(self, attr_name, None)
            if field:
                # Template content is in a model field
                templates[name] = Template(field)
            else:
                # Model field is empty - look for a file template
                template_name = getattr(self, "%s_file" % attr_name) % code
                try:
                    templates[name] = get_template(template_name)
                except TemplateDoesNotExist:
                    templates[name] = None

        # Pass base URL for serving images within HTML emails
        if ctx is None:
            ctx = {}
        ctx['static_base_url'] = getattr(settings, 'OSCAR_STATIC_BASE_URL', None)

        messages = {}
        for name, template in templates.items():
            messages[name] = template.render(Context(ctx)) if template else ''

        # Ensure the email subject doesn't contain any newlines
        messages['subject'] = messages['subject'].replace("\n", "")

        return messages

    def __unicode__(self):
        return self.name

    def is_order_related(self):
        return self.category == self.ORDER_RELATED

    def is_user_related(self):
        return self.category == self.USER_RELATED


class AbstractNotification(models.Model):
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
        abstract = True

    def __unicode__(self):
        return self.subject

    def archive(self):
        self.location = self.ARCHIVE
        self.save()

    @property
    def is_read(self):
        return self.date_read is not None
