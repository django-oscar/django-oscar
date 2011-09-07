from decimal import Decimal
import datetime

from django.core import exceptions
from django.db import models
from django.utils.translation import ugettext as _


class AbstractVoucher(models.Model):
    """
    A voucher.  This is simply a link to a collection of offers

    Note that there are three possible "usage" models:
    (a) Single use
    (b) Multi-use
    (c) Once per customer
    """
    name = models.CharField(_("Name"), max_length=128,
        help_text=_("""This will be shown in the checkout and basket once the voucher is entered"""))
    code = models.CharField(_("Code"), max_length=128, db_index=True, unique=True,
        help_text=_("""Case insensitive / No spaces allowed"""))
    offers = models.ManyToManyField('offer.ConditionalOffer', related_name='vouchers', 
                                    limit_choices_to={'offer_type': "Voucher"})

    SINGLE_USE, MULTI_USE, ONCE_PER_CUSTOMER = ('Single use', 'Multi-use', 'Once per customer')
    USAGE_CHOICES = (
        (SINGLE_USE, _("Can be used once by one customer")),
        (MULTI_USE, _("Can be used multiple times by multiple customers")),
        (ONCE_PER_CUSTOMER, _("Can only be used once per customer")),
    )
    usage = models.CharField(_("Usage"), max_length=128, choices=USAGE_CHOICES, default=MULTI_USE)

    start_date = models.DateField()
    end_date = models.DateField()

    # Summary information
    num_basket_additions = models.PositiveIntegerField(default=0)
    num_orders = models.PositiveIntegerField(default=0)
    total_discount = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    
    date_created = models.DateField(auto_now_add=True)

    class Meta:
        get_latest_by = 'date_created'
        abstract = True

    def __unicode__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise exceptions.ValidationError(_('End date should be later than start date'))

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super(AbstractVoucher, self).save(*args, **kwargs)

    def is_active(self, test_date=None):
        """
        Tests whether this voucher is currently active.
        """
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date

    def is_available_to_user(self, user=None):
        """
        Tests whether this voucher is available to the passed user.
        
        Returns a tuple of a boolean for whether it is successulf, and a message
        """
        is_available, message = False, ''
        if self.usage == self.SINGLE_USE:
            is_available = self.applications.count() == 0
            if not is_available:
                message = "This voucher has already been used"
        elif self.usage == self.MULTI_USE:
            is_available = True
        elif self.usage == self.ONCE_PER_CUSTOMER:
            if not user.is_authenticated():
                is_available = False
                message = "This voucher is only available to signed in users"
            else:
                is_available = self.applications.filter(voucher=self, user=user).count() == 0
                if not is_available:
                    message = "You have already used this voucher in a previous order"
        return is_available, message
    
    def record_usage(self, order, user):
        """
        Records a usage of this voucher in an order.
        """
        self.applications.create(voucher=self, order=order, user=user)
        
        
class AbstractVoucherApplication(models.Model):
    """
    For tracking how often a voucher has been used
    """
    voucher = models.ForeignKey('voucher.Voucher', related_name="applications")
    # It is possible for an anonymous user to apply a voucher so we need to allow
    # the user to be nullable
    user = models.ForeignKey('auth.User', blank=True, null=True)
    order = models.ForeignKey('order.Order')
    date_created = models.DateField(auto_now_add=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"'%s' used by '%s'" % (self.voucher, self.user)        
