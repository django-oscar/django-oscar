import zlib

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

class AbstractBasket(models.Model):
    """
    Basket object
    """
    # Baskets can be anonymously owned
    owner = models.ForeignKey(User, related_name='baskets', null=True)
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
    
    def add_product(self, item, quantity=1):
        """
        Convenience method for adding a line
        """
        self.lines.create(basket=self, product=item, quantity=quantity)
    
    def get_num_lines(self):
        """
        Returns number of lines within this basket
        """
        return self.lines.all().count()
    
    def get_num_items(self):
        """
        Returns the number of items in the basket
        """
        return reduce(lambda num,line: num+line.quantity, self.lines.all(), 0)
    
    def __unicode__(self):
        return "%s basket (owner: %s)" % (self.status, self.owner)
    
class AbstractLine(models.Model):
    """
    A line of a basket (product and a quantity)
    """
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
        
    def __unicode__(self):
        return "%s, Product '%s', quantity %d" % (self.basket, self.product, self.quantity)
    
class AbstractLineAttribute(models.Model):
    line = models.ForeignKey('basket.Line', related_name='attributes')
    type = models.CharField(max_length=128)
    value = models.CharField(max_length=255)    
    
    def get_hash(self):
        return zlib.crc32(self.type + self.value)
    
    class Meta:
        abstract = True
    
