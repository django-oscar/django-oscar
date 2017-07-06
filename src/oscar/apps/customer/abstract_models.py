from django.utils import six

from django.conf import settings
from django.contrib.auth import models as auth_models
from django.db import models
from django.template import Template, Context, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from oscar.apps.customer.managers import CommunicationTypeManager
from oscar.core.compat import AUTH_USER_MODEL
from oscar.models.fields import AutoSlugField


class UserManager(auth_models.BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given username, email and
        password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = UserManager.normalize_email(email)
        user = self.model(
            email=email, is_staff=False, is_active=True,
            is_superuser=False,
            last_login=now, date_joined=now, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class AbstractUser(auth_models.AbstractBaseUser,
                   auth_models.PermissionsMixin):
    """
    An abstract base user suitable for use in Oscar projects.

    This is basically a copy of the core AbstractUser model but without a
    username field
    """
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(
        _('First name'), max_length=255, blank=True)
    last_name = models.CharField(
        _('Last name'), max_length=255, blank=True)
    is_staff = models.BooleanField(
        _('Staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(
        _('Active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'),
                                       default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        abstract = True
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def handle_order_shipped_to(self, shipping_address):
        """
        Put the shipping address in the user's address book, or if it's there
        already, increase its usage counter to track which addresses are used
        most often for orders.
        """
        try:
            user_address = self.addresses.get(
                hash=shipping_address.generate_hash())
        except self.addresses.model.DoesNotExist:
            # Create a new user address
            user_address = self.addresses.model(user=self)
            shipping_address.populate_alternative_model(user_address)

        user_address.num_orders += 1
        user_address.save()


@python_2_unicode_compatible
class AbstractEmail(models.Model):
    """
    This is a record of all emails sent to a customer.
    Normally, we only record order-related emails.
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='emails',
                             verbose_name=_("User"))
    subject = models.TextField(_('Subject'), max_length=255)
    body_text = models.TextField(_("Body Text"))
    body_html = models.TextField(_("Body HTML"), blank=True)
    date_sent = models.DateTimeField(_("Date Sent"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'customer'
        verbose_name = _('Email')
        verbose_name_plural = _('Emails')

    def __str__(self):
        return _(u"Email to %(user)s with subject '%(subject)s'") % {
            'user': self.user.get_username(), 'subject': self.subject}


@python_2_unicode_compatible
class AbstractCommunicationEventType(models.Model):
    """
    A 'type' of communication.  Like a order confirmation email.
    """

    #: Code used for looking up this event programmatically.
    # e.g. PASSWORD_RESET. AutoSlugField uppercases the code for us because
    # it's a useful convention that's been enforced in previous Oscar versions
    code = AutoSlugField(
        _('Code'), max_length=128, unique=True, populate_from='name',
        separator=six.u("_"), uppercase=True, editable=True,
        help_text=_("Code used for looking up this event programmatically"))

    #: Name is the friendly description of an event for use in the admin
    name = models.CharField(
        _('Name'), max_length=255,
        help_text=_("This is just used for organisational purposes"))

    # We allow communication types to be categorised
    # For backwards-compatibility, the choice values are quite verbose
    ORDER_RELATED = 'Order related'
    USER_RELATED = 'User related'
    CATEGORY_CHOICES = (
        (ORDER_RELATED, _('Order related')),
        (USER_RELATED, _('User related'))
    )

    category = models.CharField(
        _('Category'), max_length=255, default=ORDER_RELATED,
        choices=CATEGORY_CHOICES)

    # Template content for emails
    # NOTE: There's an intentional distinction between None and ''. None
    # instructs Oscar to look for a file-based template, '' is just an empty
    # template.
    email_subject_template = models.CharField(
        _('Email Subject Template'), max_length=255, blank=True, null=True)
    email_body_template = models.TextField(
        _('Email Body Template'), blank=True, null=True)
    email_body_html_template = models.TextField(
        _('Email Body HTML Template'), blank=True, null=True,
        help_text=_("HTML template"))

    # Template content for SMS messages
    sms_template = models.CharField(_('SMS Template'), max_length=170,
                                    blank=True, null=True,
                                    help_text=_("SMS template"))

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
        app_label = 'customer'
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
        templates = {'subject': 'email_subject_template',
                     'body': 'email_body_template',
                     'html': 'email_body_html_template',
                     'sms': 'sms_template'}
        for name, attr_name in templates.items():
            field = getattr(self, attr_name, None)
            if field is not None:
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
        ctx['static_base_url'] = getattr(
            settings, 'OSCAR_STATIC_BASE_URL', None)

        messages = {}
        for name, template in templates.items():
            messages[name] = template.render(Context(ctx)) if template else ''

        # Ensure the email subject doesn't contain any newlines
        messages['subject'] = messages['subject'].replace("\n", "")
        messages['subject'] = messages['subject'].replace("\r", "")

        return messages

    def __str__(self):
        return self.name

    def is_order_related(self):
        return self.category == self.ORDER_RELATED

    def is_user_related(self):
        return self.category == self.USER_RELATED


@python_2_unicode_compatible
class AbstractNotification(models.Model):
    recipient = models.ForeignKey(AUTH_USER_MODEL,
                                  related_name='notifications', db_index=True)

    # Not all notifications will have a sender.
    sender = models.ForeignKey(AUTH_USER_MODEL, null=True)

    # HTML is allowed in this field as it can contain links
    subject = models.CharField(max_length=255)
    body = models.TextField()

    # Some projects may want to categorise their notifications.  You may want
    # to use this field to show a different icons next to the notification.
    category = models.CharField(max_length=255, blank=True)

    INBOX, ARCHIVE = 'Inbox', 'Archive'
    choices = (
        (INBOX, _('Inbox')),
        (ARCHIVE, _('Archive')))
    location = models.CharField(max_length=32, choices=choices,
                                default=INBOX)

    date_sent = models.DateTimeField(auto_now_add=True)
    date_read = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        app_label = 'customer'
        ordering = ('-date_sent',)
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return self.subject

    def archive(self):
        self.location = self.ARCHIVE
        self.save()
    archive.alters_data = True

    @property
    def is_read(self):
        return self.date_read is not None
