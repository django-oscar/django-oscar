from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

from oscar.offer.managers import ActiveOfferManager


class AbstractConditionalOffer(models.Model):
    u"""
    A conditional offer (eg buy 1, get 10% off)
    """
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    condition = models.OneToOneField('offer.Condition')
    benefit = models.OneToOneField('offer.Benefit')
    start_date = models.DateField()
    end_date = models.DateField()
    priority = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    class Meta:
        ordering = ['priority']
        abstract = True
        
    def is_active(self, test_date=None):
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date
        

class AbstractCondition(models.Model):
    COUNT, VALUE = ("Count", "Value")
    TYPE_CHOICES = (
        (COUNT, _("Depends on number of items in basket that are in condition range")),
        (VALUE, _("Depends on value of items in basket that are in condition range")),
    )
    range = models.ForeignKey('offer.Range')
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = models.DecimalField(decimal_places=2, max_digits=12)
    
    class Meta:
        abstract = True
    
    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition.  This is
        stubbed in this top-class object.  The subclassing proxies are
        responsible for implementing it correctly.
        """
        return False
    

class AbstractBenefit(models.Model):
    PERCENTAGE, FIXED = ("Percentage", "Absolute")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a % of the product's value")),
        (FIXED, _("Discount is a fixed amount off the product's value")),
    )
    range = models.ForeignKey('offer.Range')
    type = models.CharField(max_length=128, choices=TYPE_CHOICES)
    value = models.DecimalField(decimal_places=2, max_digits=12)
    
    # If this is not set, then there is no upper limit on how many products 
    # can be discounted by this benefit.
    max_affected_items = models.PositiveIntegerField(blank=True, null=True)
    
    def apply(self, basket):
        return basket


class AbstractRange(models.Model):
    name = models.CharField(max_length=128)
    includes_all_products = models.BooleanField(default=False)
    included_products = models.ManyToManyField('product.Item', related_name='includes', blank=True)
    excluded_products = models.ManyToManyField('product.Item', related_name='excludes', blank=True)
    
    class Meta:
        abstract = True
        
    def contains_product(self, product):
        if self.includes_all_products:
            return True
        return False
