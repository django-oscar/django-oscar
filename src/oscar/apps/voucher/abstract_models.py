from decimal import Decimal

from django.core import exceptions
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from oscar.apps.voucher.utils import get_unused_code
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import get_model


class AbstractVoucherSet(models.Model):
    """A collection of vouchers (potentially auto-generated)

    a VoucherSet is a group of voucher that are generated
    automatically.

    - count: the minimum number of vouchers in the set. If this is kept at
    zero, vouchers are created when and as needed.

    - code_length: the length of the voucher code. Codes are by default created
    with groups of 4 characters: XXXX-XXXX-XXXX. The dashes (-) do not count for
    the code_length.

    - :py:attr:`.start_datetime` and :py:attr:`.end_datetime` together define the validity
      range for all vouchers in the set.
    """

    name = models.CharField(verbose_name=_('Name'), max_length=100)
    count = models.PositiveIntegerField(verbose_name=_('Number of vouchers'))
    code_length = models.IntegerField(
        verbose_name=_('Length of Code'), default=12)
    description = models.TextField(verbose_name=_('Description'))
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    start_datetime = models.DateTimeField(_('Start datetime'))
    end_datetime = models.DateTimeField(_('End datetime'))

    offer = models.OneToOneField(
        'offer.ConditionalOffer', related_name='voucher_set',
        verbose_name=_("Offer"), limit_choices_to={'offer_type': "Voucher"},
        on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'voucher'
        get_latest_by = 'date_created'
        ordering = ['-date_created']
        verbose_name = _("VoucherSet")
        verbose_name_plural = _("VoucherSets")

    def __str__(self):
        return self.name

    def generate_vouchers(self):
        """Generate vouchers for this set"""
        current_count = self.vouchers.count()
        for i in range(current_count, self.count):
            self.add_new()

    def add_new(self):
        """Add a new voucher to this set"""
        Voucher = get_model('voucher', 'Voucher')
        code = get_unused_code(length=self.code_length)
        voucher = Voucher.objects.create(
            name=self.name,
            code=code,
            voucher_set=self,
            usage=Voucher.SINGLE_USE,
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime)

        if self.offer:
            voucher.offers.add(self.offer)

        return voucher

    def is_active(self, test_datetime=None):
        """Test whether this voucher set is currently active. """
        test_datetime = test_datetime or timezone.now()
        return self.start_datetime <= test_datetime <= self.end_datetime

    def save(self, *args, **kwargs):
        self.count = max(self.count, self.vouchers.count())
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.generate_vouchers()
            self.vouchers.update(
                start_datetime=self.start_datetime,
                end_datetime=self.end_datetime
            )

    @property
    def num_basket_additions(self):
        value = self.vouchers.aggregate(result=Sum('num_basket_additions'))
        return value['result']

    @property
    def num_orders(self):
        value = self.vouchers.aggregate(result=Sum('num_orders'))
        return value['result']

    @property
    def total_discount(self):
        value = self.vouchers.aggregate(result=Sum('total_discount'))
        return value['result']


class AbstractVoucher(models.Model):
    """
    A voucher.  This is simply a link to a collection of offers.

    Note that there are three possible "usage" modes:
    (a) Single use
    (b) Multi-use
    (c) Once per customer

    Oscar enforces those modes by creating VoucherApplication
    instances when a voucher is used for an order.
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

    start_datetime = models.DateTimeField(_('Start datetime'), db_index=True)
    end_datetime = models.DateTimeField(_('End datetime'), db_index=True)

    # Reporting information. Not used to enforce any consumption limits.
    num_basket_additions = models.PositiveIntegerField(
        _("Times added to basket"), default=0)
    num_orders = models.PositiveIntegerField(_("Times on orders"), default=0)
    total_discount = models.DecimalField(
        _("Total discount"), decimal_places=2, max_digits=12,
        default=Decimal('0.00'))

    voucher_set = models.ForeignKey(
        'voucher.VoucherSet', null=True, blank=True, related_name='vouchers',
        on_delete=models.CASCADE
    )

    date_created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'voucher'
        ordering = ['-date_created']
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
        super().save(*args, **kwargs)

    def is_active(self, test_datetime=None):
        """
        Test whether this voucher is currently active.
        """
        test_datetime = test_datetime or timezone.now()
        return self.start_datetime <= test_datetime <= self.end_datetime

    def is_expired(self):
        """
        Test whether this voucher has passed its expiration date
        """
        now = timezone.now()
        return self.end_datetime < now

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
            if not user.is_authenticated:
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

    def is_available_for_basket(self, basket):
        """
        Tests whether this voucher is available to the passed basket.

        Returns a tuple of a boolean for whether it is successful, and a
        availability message.
        """
        is_available, message = self.is_available_to_user(user=basket.owner)
        if not is_available:
            return False, message

        is_available, message = False, _("This voucher is not available for this basket")
        for offer in self.offers.all():
            if offer.is_condition_satisfied(basket=basket):
                is_available = True
                message = ''
                break
        return is_available, message

    def record_usage(self, order, user):
        """
        Records a usage of this voucher in an order.
        """
        if user.is_authenticated:
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
        """
        Returns the first offer's benefit instance.

        A voucher is commonly only linked to one offer. In that case,
        this helper can be used for convenience.
        """
        return self.offers.first().benefit


class AbstractVoucherApplication(models.Model):
    """
    For tracking how often a voucher has been used in an order.

    This is used to enforce the voucher usage mode in
    Voucher.is_available_to_user, and created in Voucher.record_usage.
    """
    voucher = models.ForeignKey(
        'voucher.Voucher',
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Voucher"))

    # It is possible for an anonymous user to apply a voucher so we need to
    # allow the user to be nullable
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("User"))
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        verbose_name=_("Order"))
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'voucher'
        ordering = ['-date_created']
        verbose_name = _("Voucher Application")
        verbose_name_plural = _("Voucher Applications")

    def __str__(self):
        return _("'%(voucher)s' used by '%(user)s'") % {
            'voucher': self.voucher,
            'user': self.user}
