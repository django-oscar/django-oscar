from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _


class Basket(models.Model):
    """
    Main basket object
    """
    OPEN, MERGED, SUBMITTED = ("Open", "Merged", "Submitted")
    STATUS_CHOICES = (
        (OPEN, _("Open - currently active")),
        (MERGED, _("Merged - superceded by another basket")),
        (SUBMITTED, _("Submitted - has been ordered at the checkout")),
    )
    
    owner = models.ForeignKey(User, related_name='baskets')
    status = models.CharField(max_length=128, default=OPEN, choices=STATUS_CHOICES)
    created_date = models.DateTimeField(auto_now_add=True)
    
    
class Line(models.Model):
    basket = models.ForeignKey('basket.Basket', related_name='lines')
    product = models.ForeignKey('product.Item')
    vouchers = models.ManyToManyField('offer.Voucher')
    
    
class LineAttribute(models.Model):
    line = models.ForeignKey('basket.Line', related_name='attributes')
    type = models.CharField(max_length=128)
    value = models.CharField(max_length=255)    
    
