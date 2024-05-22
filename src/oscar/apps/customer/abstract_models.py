from django.contrib.auth import models as auth_models
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from oscar.core.compat import AUTH_USER_MODEL


class UserManager(auth_models.BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and
        password.
        """
        now = timezone.now()
        if not email:
            raise ValueError("The given email must be set")
        email = UserManager.normalize_email(email)
        user = self.model(
            email=email,
            is_staff=False,
            is_active=True,
            is_superuser=False,
            last_login=now,
            date_joined=now,
            **extra_fields
        )

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


class AbstractUser(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    """
    An abstract base user suitable for use in Oscar projects.

    This is basically a copy of the core AbstractUser model but without a
    username field
    """

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("First name"), max_length=255, blank=True)
    last_name = models.CharField(_("Last name"), max_length=255, blank=True)
    is_staff = models.BooleanField(
        _("Staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as "
            "active. Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta:
        abstract = True
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Return the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Send an email to this user.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def _migrate_alerts_to_user(self):
        """
        Transfer any active alerts linked to a user's email address to the
        newly registered user.
        """
        # pylint: disable=no-member
        ProductAlert = self.alerts.model
        alerts = ProductAlert.objects.filter(
            email=self.email, status=ProductAlert.ACTIVE
        )
        alerts.update(user=self, key="", email="")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Migrate any "anonymous" product alerts to the registered user
        # Ideally, this would be done via a post-save signal. But we can't
        # use get_user_model to wire up signals to custom user models
        # see Oscar ticket #1127, Django ticket #19218
        self._migrate_alerts_to_user()


class AbstractProductAlert(models.Model):
    """
    An alert for when a product comes back in stock
    """

    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)

    # A user is only required if the notification is created by a
    # registered user, anonymous users will only have an email address
    # attached to the notification
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name=_("User"),
    )
    email = models.EmailField(_("Email"), db_index=True, blank=True)

    # This key are used to confirm and cancel alerts for anon users
    key = models.CharField(_("Key"), max_length=128, blank=True, db_index=True)

    # An alert can have two different statuses for authenticated
    # users ``ACTIVE`` and ``CANCELLED`` and anonymous users have an
    # additional status ``UNCONFIRMED``. For anonymous users a confirmation
    # and unsubscription key are generated when an instance is saved for
    # the first time and can be used to confirm and unsubscribe the
    # notifications.
    UNCONFIRMED, ACTIVE, CANCELLED, CLOSED = (
        "Unconfirmed",
        "Active",
        "Cancelled",
        "Closed",
    )
    STATUS_CHOICES = (
        (UNCONFIRMED, _("Not yet confirmed")),
        (ACTIVE, _("Active")),
        (CANCELLED, _("Cancelled")),
        (CLOSED, _("Closed")),
    )
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default=ACTIVE
    )

    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, db_index=True
    )
    date_confirmed = models.DateTimeField(_("Date confirmed"), blank=True, null=True)
    date_cancelled = models.DateTimeField(_("Date cancelled"), blank=True, null=True)
    date_closed = models.DateTimeField(_("Date closed"), blank=True, null=True)

    class Meta:
        abstract = True
        app_label = "customer"
        ordering = ["-date_created"]
        verbose_name = _("Product alert")
        verbose_name_plural = _("Product alerts")

    @property
    def is_anonymous(self):
        return self.user is None

    @property
    def can_be_confirmed(self):
        return self.status == self.UNCONFIRMED

    @property
    def can_be_cancelled(self):
        return self.status in (self.ACTIVE, self.UNCONFIRMED)

    @property
    def is_cancelled(self):
        return self.status == self.CANCELLED

    @property
    def is_active(self):
        return self.status == self.ACTIVE

    def confirm(self):
        self.status = self.ACTIVE
        self.date_confirmed = timezone.now()
        self.save()

    confirm.alters_data = True

    def cancel(self):
        self.status = self.CANCELLED
        self.date_cancelled = timezone.now()
        self.save()

    cancel.alters_data = True

    def close(self):
        self.status = self.CLOSED
        self.date_closed = timezone.now()
        self.save()

    close.alters_data = True

    def get_email_address(self):
        if self.user:
            return self.user.email
        else:
            return self.email

    def save(self, *args, **kwargs):
        if not self.id and not self.user:
            self.key = self.get_random_key()
            self.status = self.UNCONFIRMED
        # Ensure date fields get updated when saving from modelform (which just
        # calls save, and doesn't call the methods cancel(), confirm() etc).
        if self.status == self.CANCELLED and self.date_cancelled is None:
            self.date_cancelled = timezone.now()
        if not self.user and self.status == self.ACTIVE and self.date_confirmed is None:
            self.date_confirmed = timezone.now()
        if self.status == self.CLOSED and self.date_closed is None:
            self.date_closed = timezone.now()

        return super().save(*args, **kwargs)

    def get_random_key(self):
        return get_random_string(
            length=40, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789"
        )

    def get_confirm_url(self):
        return reverse("customer:alerts-confirm", kwargs={"key": self.key})

    def get_cancel_url(self):
        return reverse("customer:alerts-cancel-by-key", kwargs={"key": self.key})
