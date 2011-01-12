import zlib

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
    
    def is_empty(self):
        return self.get_num_lines() == 0
    
    def get_num_lines(self):
        """
        Returns number of lines within this basket
        """
        return len(self.lines.all())
    
    def get_num_items(self):
        return reduce(lambda num,line: num+line.quantity, self.lines)
    
    def __unicode__(self):
        return "%s basket (owner: %s)" % (self.status, self.owner)
    
class AbstractLine(models.Model):
    basket = models.ForeignKey('basket.Basket', related_name='lines')
    product = models.ForeignKey('product.Item')
    quantity = models.PositiveIntegerField(default=1)
    
    def get_hash(self):
        """
        Need a line hash as lines are stored as separate items
        when persisted as an order.  The line ID helps distinguish
        between two items which are variants of the same product and
        so should not be treated as the same line.
        
        This is a hash of the line attributes.
        """
        attribute_string = "_".join([attribute.get_hash() for attributes in self.attributes])
        return zlib.crc32(attribute_string)
        
    
    class Meta:
        abstract = True
    
class AbstractLineAttribute(models.Model):
    line = models.ForeignKey('basket.Line', related_name='attributes')
    type = models.CharField(max_length=128)
    value = models.CharField(max_length=255)    
    
    def get_hash(self):
        return zlib.crc32(self.type + self.value)
    
    class Meta:
        abstract = True
    
