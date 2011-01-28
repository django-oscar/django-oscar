from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist

from oscar.basket.managers import OpenBasketManager, SavedBasketManager

# Basket statuses
OPEN, MERGED, SAVED, SUBMITTED = ("Open", "Merged", "Saved", "Submitted")


class AbstractBasket(models.Model):
    """
    Basket object
    """
    # Baskets can be anonymously owned (which are then merged
    owner = models.ForeignKey(User, related_name='baskets', null=True)
    STATUS_CHOICES = (
        (OPEN, _("Open - currently active")),
        (MERGED, _("Merged - superceded by another basket")),
        (SAVED, _("Saved - for items to be purchased later")),
        (SUBMITTED, _("Submitted - has been ordered at the checkout")),
    )
    status = models.CharField(_("Status"), max_length=128, default=OPEN, choices=STATUS_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_merged = models.DateTimeField(null=True, blank=True)
    date_submitted = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    # Custom manager for searching open baskets only
    objects = models.Manager()
    open = OpenBasketManager()
    saved = SavedBasketManager()
    
    # ============    
    # Manipulation
    # ============
    
    def merge(self, basket):
        """
        Merges another basket with this one
        """
        for line_to_merge in basket.lines.all():
            # Check if the current basket has a matching line and update
            # the quantity.
            try:
                line = self.lines.get(line_reference=line_to_merge.line_reference)
                line.quantity += line_to_merge.quantity
                line.save()
                line_to_merge.delete()
            except ObjectDoesNotExist:
                line_to_merge.basket = self
                line_to_merge.save()
        basket.status = MERGED
        basket.save()
    
    def flush(self):
        self.lines.all().delete()
    
    def add_product(self, item, quantity=1):
        """
        Convenience method for adding products to a basket
        """
        try:
            line = self.lines.get(product=item)
            line.quantity += quantity
            line.save()
        except ObjectDoesNotExist:
            self.lines.create(basket=self, product=item, quantity=quantity)
    
    def add_line(self, line):
        """
        For adding a line from another basket to this one
        """
        line.basket = self
        line.save()
    
    # ==========
    # Properties
    # ==========
    
    @property
    def is_empty(self):
        return self.num_lines == 0
    
    @property
    def total_excl_tax(self):
        return self._get_total('line_price_excl_tax')
    
    @property
    def total_tax(self):
        return self._get_total('line_tax')
    
    @property
    def total_incl_tax(self):
        return self._get_total('line_price_incl_tax')
    
    @property
    def num_lines(self):
        return self.lines.all().count()
    
    @property
    def num_items(self):
        """
        Returns the number of items in the basket
        """
        return reduce(lambda num,line: num+line.quantity, self.lines.all(), 0)
    
    def _get_total(self, property):
        """
        For executing a named method on each line of the basket
        and returning the total.
        """
        total = Decimal('0.00')
        for line in self.lines.all():
            total += getattr(line, property)
        return total
    
    def __unicode__(self):
        return u"%s basket (owner: %s, lines: %d)" % (self.status, self.owner, self.num_lines)
    
    
class AbstractLine(models.Model):
    """
    A line of a basket (product and a quantity)
    """
    basket = models.ForeignKey('basket.Basket', related_name='lines')
    # This is to determine which products belong to the same line
    # We can't just use product.id as you can have customised products
    # which should be treated as separate lines.  Set as a 
    # SlugField as it is included in the path for certain views.
    line_reference = models.SlugField(max_length=128, db_index=True)
    product = models.ForeignKey('product.Item')
    quantity = models.PositiveIntegerField(default=1)
    
    def _get_stockrecord_property(self, property):
        if not self.product.stockrecord:
            return None
        else:
            return getattr(self.product.stockrecord, property)
    
    @property
    def unit_price_excl_tax(self):
        return self._get_stockrecord_property('price_excl_tax')
    
    @property
    def unit_tax(self):
        return self._get_stockrecord_property('price_tax')
    
    @property
    def unit_price_incl_tax(self):
        return self._get_stockrecord_property('price_incl_tax')
    
    @property
    def line_price_excl_tax(self):
       return self.quantity * self.unit_price_excl_tax
       
    @property    
    def line_tax(self):
        return self.quantity * self.unit_tax
    
    @property
    def line_price_incl_tax(self):
        return self.quantity * self.unit_price_incl_tax
    
    def save(self, *args, **kwargs):
        if self.quantity == 0:
            return self.delete(*args, **kwargs)
        if not self.line_reference:
            # If no line reference explicitly set, then use the product ID
            self.line_reference = self.product.id
        super(AbstractLine, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        unique_together = ("basket", "line_reference")
        
    def __unicode__(self):
        return u"%s, Product '%s', quantity %d" % (self.basket, self.product, self.quantity)
    
class AbstractLineAttribute(models.Model):
    """
    An attribute of a basket line
    """
    line = models.ForeignKey('basket.Line', related_name='attributes')
    type = models.CharField(_("Type"), max_length=128)
    value = models.CharField(_("Value"), max_length=255)    
    
    def get_hash(self):
        return zlib.crc32(self.type + self.value)
    
    class Meta:
        abstract = True
    
