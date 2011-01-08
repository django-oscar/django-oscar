from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

class AbstractBasket(models.Model):
    """
    Basket object
    """
    owner = models.ForeignKey(User, related_name='baskets')
    OPEN, MERGED, SUBMITTED = ("Open", "Merged", "Submitted")
    STATUS_CHOICES = (
        (OPEN, _("Open - currently active")),
        (MERGED, _("Merged - superceded by another basket")),
        (SUBMITTED, _("Submitted - has been ordered at the checkout")),
    )
    status = models.CharField(max_length=128, default=OPEN, choices=STATUS_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_merged = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
class AbstractLine(models.Model):
    basket = models.ForeignKey('basket.Basket', related_name='lines')
    product = models.ForeignKey('product.Item')
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        abstract = True
    
class AbstractLineAttribute(models.Model):
    line = models.ForeignKey('basket.Line', related_name='attributes')
    type = models.CharField(max_length=128)
    value = models.CharField(max_length=255)    
    
    class Meta:
        abstract = True
    
