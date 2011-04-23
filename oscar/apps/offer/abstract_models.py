from decimal import Decimal
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

from oscar.apps.offer.managers import ActiveOfferManager

SITE, VOUCHER, USER, SESSION = ("Site", "Voucher", "User", "Session")

class AbstractConditionalOffer(models.Model):
    u"""
    A conditional offer (eg buy 1, get 10% off)
    """
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)

    # Offers come in a few different types:
    # (a) Offers that are available to all customers on the site.  Eg a 
    #     3-for-2 offer.
    # (b) Offers that are linked to a voucher, and only become available once
    #     that voucher has been applied to the basket
    # (c) Offers that are linked to a user.  Eg, all students get 10% off.  The code
    #     to apply this offer needs to be coded
    # (d) Session offers - these are temporarily available to a user after some trigger 
    #     event.  Eg, users coming from some affiliate site get 10% off.     
    TYPE_CHOICES = (
        (SITE, "Site offer - available to all users"),
        (VOUCHER, "Voucher offer - only available after entering the appropriate voucher code"),
        (USER, "User offer - available to certain types of user"),
        (SESSION, "Session offer - temporary offer, available for a user for the duration of their session"),
    )
    offer_type = models.CharField(_("Type"), choices=TYPE_CHOICES, default=SITE, max_length=128)

    condition = models.ForeignKey('offer.Condition')
    benefit = models.ForeignKey('offer.Benefit')

    # Range of availability.  Note that if this is a voucher offer, then these
    # dates are ignored and only the dates from the voucher are used to determine 
    # availability.
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # Some complicated situations require offers to be applied in a set order.
    priority = models.IntegerField(default=0, help_text="The highest priority offers are applied first")

    # We track some information on usage
    total_discount = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    
    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    # We need to track the voucher that this offer came from (if it is a voucher offer)
    _voucher = None

    class Meta:
        ordering = ['-priority']
        abstract = True
        
    def __unicode__(self):
        return self.name    
        
    def is_active(self, test_date=None):
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date
    
    def is_condition_satisfied(self, basket):
        return self._proxy_condition().is_satisfied(basket)
        
    def apply_benefit(self, basket):
        u"""
        Applies the benefit to the given basket and returns the discount.
        """
        if not self.is_condition_satisfied(basket):
            return Decimal('0.00')
        return self._proxy_benefit().apply(basket, self._proxy_condition())
        
    def set_voucher(self, voucher):
        self._voucher = voucher
        
    def get_voucher(self):
        return self._voucher        
        
    def _proxy_condition(self):
        u"""
        Returns the appropriate proxy model for the condition
        """
        return self.condition
    
    def _proxy_benefit(self):
        u"""
        Returns the appropriate proxy model for the benefit
        """
        return self.benefit
        

class AbstractCondition(models.Model):
    COUNT, VALUE, COVERAGE = ("Count", "Value", "Coverage")
    TYPE_CHOICES = (
        (COUNT, _("Depends on number of items in basket that are in condition range")),
        (VALUE, _("Depends on value of items in basket that are in condition range")),
        (COVERAGE, _("Needs to contain a set number of DISTINCT items from the condition range"))
    )
    range = models.ForeignKey('offer.Range')
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = models.DecimalField(decimal_places=2, max_digits=12)
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        if self.type == self.COUNT:
            return u"Basket includes %d item(s) from %s" % (self.value, str(self.range).lower())
        elif self.type == self.COVERAGE:
            return u"Basket includes %d distinct products from %s" % (self.value, str(self.range).lower())
        return u"Basket includes %.2f value from %s" % (self.value, str(self.range).lower())
    
    def consume_items(self, basket):
        pass
    
    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition.  This is
        stubbed in this top-class object.  The subclassing proxies are
        responsible for implementing it correctly.
        """
        return False
    

class AbstractBenefit(models.Model):
    PERCENTAGE, FIXED, MULTIBUY, FIXED_PRICE = ("Percentage", "Absolute", "Multibuy", "Fixed price")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a % of the product's value")),
        (FIXED, _("Discount is a fixed amount off the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free")),
        (FIXED_PRICE, _("Get the products that meet the condition for a fixed price")),
    )
    range = models.ForeignKey('offer.Range', null=True, blank=True)
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = models.DecimalField(decimal_places=2, max_digits=12)
    
    # If this is not set, then there is no upper limit on how many products 
    # can be discounted by this benefit.
    max_affected_items = models.PositiveIntegerField(blank=True, null=True, help_text="""Set this
        to prevent the discount consuming all items within the range that are in the basket.""")
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        if self.type == self.PERCENTAGE:
            desc = u"%s%% discount on %s" % (self.value, str(self.range).lower())
        elif self.type == self.MULTIBUY:
            desc = u"Cheapest product is free from %s" % str(self.range)
        elif self.type == self.FIXED_PRICE:
            desc = u"The products that meet the condition are sold for %s" % self.value
        else:
            desc = u"%.2f discount on %s" % (self.value, str(self.range).lower())
        if self.max_affected_items == 1:
            desc += u" (max 1 item)"
        elif self.max_affected_items > 1:
            desc += u" (max %d items)" % self.max_affected_items
        return desc
    
    def apply(self, basket, condition=None):
        return Decimal('0.00')
    
    def clean(self):
        # All benefits need a range apart from FIXED_PRICE
        if self.type != self.FIXED_PRICE and not self.range:
            raise ValidationError("Benefits of type %s need a range" % self.type)


class AbstractRange(models.Model):
    u"""
    Represents a range of products that can be used within an offer
    """
    name = models.CharField(_("Name"), max_length=128)
    includes_all_products = models.BooleanField(default=False)
    included_products = models.ManyToManyField('product.Item', related_name='includes', blank=True)
    excluded_products = models.ManyToManyField('product.Item', related_name='excludes', blank=True)
    classes = models.ManyToManyField('product.ItemClass', related_name='classes', blank=True)
    
    __included_product_ids = None
    __excluded_product_ids = None
    __class_ids = None
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return self.name    
        
    def contains_product(self, product):
        excluded_product_ids = self._excluded_product_ids()
        if product.id in excluded_product_ids:
            return False
        if self.includes_all_products:
            return True
        if product.item_class_id in self._class_ids():
            return True    
        included_product_ids = self._included_product_ids()
        return product.id in included_product_ids
    
    def _included_product_ids(self):
        if None == self.__included_product_ids:
            self.__included_product_ids = [row['id'] for row in self.included_products.values('id')]
        return self.__included_product_ids
    
    def _excluded_product_ids(self):
        if None == self.__excluded_product_ids:
            self.__excluded_product_ids = [row['id'] for row in self.excluded_products.values('id')]
        return self.__excluded_product_ids
    
    def _class_ids(self):
        if None == self.__class_ids:
            self.__class_ids = [row['id'] for row in self.classes.values('id')]
        return self.__class_ids
        
        
class AbstractVoucher(models.Model):
    u"""
    A voucher.  This is simply a link to a collection of offers

    Note that there are three possible "usage" models:
    (a) Single use
    (b) Multi-use
    (c) Once per customer
    """
    name = models.CharField(_("Name"), max_length=128,
        help_text="""This will be shown in the checkout and basket once the voucher is entered""")
    code = models.CharField(_("Code"), max_length=128, db_index=True, unique=True,
        help_text="""Case insensitive / No spaces allowed""")
    offers = models.ManyToManyField('offer.ConditionalOFfer', related_name='vouchers', 
                                    limit_choices_to={'offer_type': VOUCHER})

    SINGLE_USE, MULTI_USE, ONCE_PER_CUSTOMER = ('Single use', 'Multi-use', 'Once per customer')
    USAGE_CHOICES = (
        (SINGLE_USE, "Can only be used by one customer"),
        (MULTI_USE, "Can only be used any number of times"),
        (ONCE_PER_CUSTOMER, "Can be used once by each customer"),
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
        abstract = True
        get_latest_by = 'date_created'

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super(AbstractVoucher, self).save(*args, **kwargs)

    def is_active(self, test_date=None):
        u"""
        Tests whether this voucher is currently active.
        """
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date

    def is_available_to_user(self, user=None):
        u"""
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
        u"""
        Records a usage of this voucher in an order.
        """
        self.applications.create(voucher=self, order=order, user=user)


class AbstractVoucherApplication(models.Model):
    u"""
    For tracking how often a voucher has been used
    """
    voucher = models.ForeignKey('offer.Voucher', related_name="applications")
    # It is possible for an anonymous user to apply a voucher so we need to allow
    # the user to be nullable
    user = models.ForeignKey('auth.User', blank=True, null=True)
    order = models.ForeignKey('order.Order')
    date_created = models.DateField(auto_now_add=True)

    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"'%s' used by '%s'" % (self.voucher, self.user)



