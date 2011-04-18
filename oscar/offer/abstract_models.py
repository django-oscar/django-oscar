from decimal import Decimal

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
    priority = models.IntegerField(default=0, help_text="The highest priority offers are applied first")
    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

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
        discount = self._proxy_benefit().apply(basket, self._proxy_condition())
        if discount > 0:
            # We need to mark the minimal set of condition products
            # as being unavailable for future offers.
            self._proxy_condition().consume_items(basket)
        return discount    
        
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
    
    def __unicode__(self):
        if self.type == self.COUNT:
            return u"Basket includes %d item(s) from %s" % (self.value, str(self.range).lower())
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
    PERCENTAGE, FIXED, MULTIBUY = ("Percentage", "Absolute", "Multibuy")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a % of the product's value")),
        (FIXED, _("Discount is a fixed amount off the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free"))
    )
    range = models.ForeignKey('offer.Range')
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
        else:
            desc = u"%.2f discount on %s" % (self.value, str(self.range).lower())
        if self.max_affected_items == 1:
            desc += u" (max 1 item)"
        elif self.max_affected_items > 1:
            desc += u" (max %d items)" % self.max_affected_items
        return desc
    
    def apply(self, basket, condition=None):
        return Decimal('0.00')


class AbstractRange(models.Model):
    u"""
    Represents a range of products that can be used within an offer
    """
    name = models.CharField(max_length=128)
    includes_all_products = models.BooleanField(default=False)
    included_products = models.ManyToManyField('product.Item', related_name='includes', blank=True)
    excluded_products = models.ManyToManyField('product.Item', related_name='excludes', blank=True)
    
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
        included_product_ids = self._included_product_ids()
        return product.id in included_product_ids
    
    def _included_product_ids(self):
        results = self.included_products.values('id')
        return [row['id'] for row in results]
    
    def _excluded_product_ids(self):
        results = self.excluded_products.values('id')
        return [row['id'] for row in results]
        
        
