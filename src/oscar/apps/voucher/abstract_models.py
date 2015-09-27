from decimal import Decimal

from django.core import exceptions
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from oscar.core.compat import AUTH_USER_MODEL


@python_2_unicode_compatible
class AbstractVoucher(models.Model):
    """
    A voucher.  This is simply a link to a collection of offers.

    Note that there are three possible "usage" models:
    (a) Single use
    (b) Multi-use
    (c) Once per customer
    """
    name = models.CharField(_("Name"), max_length=128,
                            help_text=_("This will be shown in the checkout"
                                        " and basket once the voucher is"
                                        " entered"))
    code = models.CharField(_("Code"), max_length=128, db_index=True,
                            unique=True, help_text=_("Case insensitive / No"
                                                     " spaces allowed"))
    offers = models.ManyToManyField(
        'offer.ConditionalOffer', related_name='vouchers',
        verbose_name=_("Offers"), limit_choices_to={'offer_type': "Voucher"})

    SINGLE_USE, MULTI_USE, ONCE_PER_CUSTOMER = (
        'Single use', 'Multi-use', 'Once per customer')
    USAGE_CHOICES = (
        (SINGLE_USE, _("Can be used once by one customer")),
        (MULTI_USE, _("Can be used multiple times by multiple customers")),
        (ONCE_PER_CUSTOMER, _("Can only be used once per customer")),
    )
    usage = models.CharField(_("Usage"), max_length=128,
                             choices=USAGE_CHOICES, default=MULTI_USE)

    start_datetime = models.DateTimeField(_('Start datetime'))
    end_datetime = models.DateTimeField(_('End datetime'))

    # Audit information
    num_basket_additions = models.PositiveIntegerField(
        _("Times added to basket"), default=0)
    num_orders = models.PositiveIntegerField(_("Times on orders"), default=0)
    total_discount = models.DecimalField(
        _("Total discount"), decimal_places=2, max_digits=12,
        default=Decimal('0.00'))

    date_created = models.DateField(auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'voucher'
        get_latest_by = 'date_created'
        verbose_name = _("Voucher")
        verbose_name_plural = _("Vouchers")

    def __str__(self):
        return self.name

    def clean(self):
        if all([self.start_datetime, self.end_datetime,
                self.start_datetime > self.end_datetime]):
            raise exceptions.ValidationError(
                _('End date should be later than start date'))

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super(AbstractVoucher, self).save(*args, **kwargs)

    def is_active(self, test_datetime=None):
        """
        Test whether this voucher is currently active.
        """
        test_datetime = test_datetime or timezone.now()
        return self.start_datetime <= test_datetime <= self.end_datetime

    def is_available_to_user(self, user=None):
        """
        Test whether this voucher is available to the passed user.

        Returns a tuple of a boolean for whether it is successful, and a
        availability message.
        """
        is_available, message = False, ''
        if self.usage == self.SINGLE_USE:
            is_available = not self.applications.exists()
            if not is_available:
                message = _("This voucher has already been used")
        elif self.usage == self.MULTI_USE:
            is_available = True
        elif self.usage == self.ONCE_PER_CUSTOMER:
            if not user.is_authenticated():
                is_available = False
                message = _(
                    "This voucher is only available to signed in users")
            else:
                is_available = not self.applications.filter(
                    voucher=self, user=user).exists()
                if not is_available:
                    message = _("You have already used this voucher in "
                                "a previous order")
        return is_available, message

    def record_usage(self, order, user):
        """
        Records a usage of this voucher in an order.
        """
        if user.is_authenticated():
            self.applications.create(voucher=self, order=order, user=user)
        else:
            self.applications.create(voucher=self, order=order)
        self.num_orders += 1
        self.save()
    record_usage.alters_data = True

    def record_discount(self, discount):
        """
        Record a discount that this offer has given
        """
        self.total_discount += discount['discount']
        self.save()
    record_discount.alters_data = True

    @property
    def benefit(self):
        return self.offers.all()[0].benefit


@python_2_unicode_compatible
class AbstractVoucherApplication(models.Model):
    """
    For tracking how often a voucher has been used
    """
    voucher = models.ForeignKey(
        'voucher.Voucher', related_name="applications",
        verbose_name=_("Voucher"))

    # It is possible for an anonymous user to apply a voucher so we need to
    # allow the user to be nullable
    user = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True,
                             verbose_name=_("User"))
    order = models.ForeignKey('order.Order', verbose_name=_("Order"))
    date_created = models.DateField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'voucher'
        verbose_name = _("Voucher Application")
        verbose_name_plural = _("Voucher Applications")

    def __str__(self):
        return _("'%(voucher)s' used by '%(user)s'") % {
            'voucher': self.voucher,
            'user': self.user}
