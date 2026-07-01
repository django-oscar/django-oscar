from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.template import engines
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from oscar.apps.communication.managers import CommunicationTypeManager
from oscar.core.compat import AUTH_USER_MODEL
from oscar.models.fields import AutoSlugField


class AbstractEmail(models.Model):
    """
    This is a record of an email sent to a customer.
    """

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emails",
        verbose_name=_("User"),
        null=True,
    )
    email = models.EmailField(_("Email Address"), null=True, blank=True)
    subject = models.TextField(_("Subject"), max_length=255)
    body_text = models.TextField(_("Body Text"))
    body_html = models.TextField(_("Body HTML"), blank=True)
    date_sent = models.DateTimeField(_("Date Sent"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "communication"
        ordering = ["-date_sent"]
        verbose_name = _("Email")
        verbose_name_plural = _("Emails")

    def __str__(self):
        if self.user:
            return _("Email to %(user)s with subject '%(subject)s'") % {
                "user": self.user.get_username(),
                "subject": self.subject,
            }
        else:
            return _("Email to %(email)s with subject '%(subject)s'") % {
                "email": self.email,
                "subject": self.subject,
            }


class AbstractCommunicationEventType(models.Model):
    """
    A 'type' of communication.  Like an order confirmation email.
    """

    #: Code used for looking up this event programmatically.
    # e.g. PASSWORD_RESET. AutoSlugField uppercases the code for us because
    # it's a useful convention that's been enforced in previous Oscar versions
    code = AutoSlugField(
        _("Code"),
        max_length=128,
        unique=True,
        populate_from="name",
        separator="_",
        uppercase=True,
        editable=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z_][0-9A-Z_]*$",
                message=_(
                    "Code can only contain the uppercase letters (A-Z), "
                    "digits, and underscores, and can't start with a digit."
                ),
            )
        ],
        help_text=_("Code used for looking up this event programmatically"),
    )

    #: Name is the friendly description of an event for use in the admin
    name = models.CharField(_("Name"), max_length=255, db_index=True)

    # We allow communication types to be categorised
    # For backwards-compatibility, the choice values are quite verbose
    ORDER_RELATED = "Order related"
    USER_RELATED = "User related"
    CATEGORY_CHOICES = (
        (ORDER_RELATED, _("Order related")),
        (USER_RELATED, _("User related")),
    )

    category = models.CharField(
        _("Category"), max_length=255, default=ORDER_RELATED, choices=CATEGORY_CHOICES
    )

    # Template content for emails
    # NOTE: There's an intentional distinction between None and ''. None
    # instructs Oscar to look for a file-based template, '' is just an empty
    # template.
    email_subject_template = models.CharField(
        _("Email Subject Template"), max_length=255, blank=True, null=True
    )
    email_body_template = models.TextField(
        _("Email Body Template"), blank=True, null=True
    )
    email_body_html_template = models.TextField(
        _("Email Body HTML Template"),
        blank=True,
        null=True,
        help_text=_("HTML template"),
    )

    # Template content for SMS messages
    sms_template = models.CharField(
        _("SMS Template"),
        max_length=170,
        blank=True,
        null=True,
        help_text=_("SMS template"),
    )

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True)

    objects = CommunicationTypeManager()

    # File templates
    email_subject_template_file = "oscar/communication/emails/commtype_%s_subject.txt"
    email_body_template_file = "oscar/communication/emails/commtype_%s_body.txt"
    email_body_html_template_file = "oscar/communication/emails/commtype_%s_body.html"
    sms_template_file = "oscar/communication/sms/commtype_%s_body.txt"

    class Meta:
        abstract = True
        app_label = "communication"
        ordering = ["name"]
        verbose_name = _("Communication event type")
        verbose_name_plural = _("Communication event types")

    def get_messages(self, ctx=None):
        """
        Return a dict of templates with the context merged in

        We look first at the field templates but fail over to
        a set of file templates that follow a conventional path.
        """
        code = self.code.lower()

        # Build a dict of message name to Template instances
        templates = {
            "subject": "email_subject_template",
            "body": "email_body_template",
            "html": "email_body_html_template",
            "sms": "sms_template",
        }
        for name, attr_name in templates.items():
            field = getattr(self, attr_name, None)
            if field is not None:
                # Template content is in a model field
                templates[name] = engines["django"].from_string(field)
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
        ctx["static_base_url"] = getattr(settings, "OSCAR_STATIC_BASE_URL", None)

        messages = {}
        for name, template in templates.items():
            # pylint: disable=no-member
            messages[name] = template.render(ctx) if template else ""

        # Ensure the email subject doesn't contain any newlines
        messages["subject"] = messages["subject"].replace("\n", "")
        messages["subject"] = messages["subject"].replace("\r", "")

        return messages

    def __str__(self):
        return self.name

    def is_order_related(self):
        return self.category == self.ORDER_RELATED

    def is_user_related(self):
        return self.category == self.USER_RELATED


class AbstractNotification(models.Model):
    recipient = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )

    # Not all notifications will have a sender.
    sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    # HTML is allowed in this field as it can contain links
    subject = models.CharField(max_length=255)
    body = models.TextField()

    INBOX, ARCHIVE = "Inbox", "Archive"
    choices = ((INBOX, _("Inbox")), (ARCHIVE, _("Archive")))
    location = models.CharField(max_length=32, choices=choices, default=INBOX)

    date_sent = models.DateTimeField(auto_now_add=True)
    date_read = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        app_label = "communication"
        ordering = ("-date_sent",)
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        return self.subject

    def archive(self):
        self.location = self.ARCHIVE
        self.save()

    archive.alters_data = True

    @property
    def is_read(self):
        return self.date_read is not None
