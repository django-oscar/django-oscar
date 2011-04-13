from decimal import Decimal
import zlib
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist

from oscar.basket.managers import OpenBasketManager, SavedBasketManager

# Basket statuses
OPEN, MERGED, SAVED, SUBMITTED = ("Open", "Merged", "Saved", "Submitted")


class AbstractBasket(models.Model):
    u"""Basket object"""
    # Baskets can be anonymously owned (which are merged if the user signs in)
    owner = models.ForeignKey('auth.User', related_name='baskets', null=True)
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
    
    # Cached queryset of lines
    _lines = None
    
    discounts = []
    
    class Meta:
        abstract = True
    
    objects = models.Manager()
    open = OpenBasketManager()
    saved = SavedBasketManager()
    
    def __unicode__(self):
        return u"%s basket (owner: %s, lines: %d)" % (self.status, self.owner, self.num_lines)
    
    def all_lines(self):
        if not self._lines:
            self._lines = self.lines.all()
        return self._lines    
    
    # ============    
    # Manipulation
    # ============
    
    def flush(self):
        u"""Remove all lines from basket."""
        self.lines_all().delete()
    
    def add_product(self, item, quantity=1, options=[]):
        u"""
        Convenience method for adding products to a basket
        
        The 'options' list should contains dicts with keys 'option' and 'value'
        which link the relevant product.Option model and string value respectively.
        """
        line_ref = self._create_line_reference(item, options)
        try:
            line = self.lines.get(line_reference=line_ref)
            line.quantity += quantity
            line.save()
        except ObjectDoesNotExist:
            line = self.lines.create(basket=self, line_reference=line_ref, product=item, quantity=quantity)
            for option_dict in options:
                line.attributes.create(line=line, option=option_dict['option'], value=option_dict['value'])

    def set_discounts(self, discounts):
        u"""
        Sets the discounts that apply to this basket.  
        
        This should be a list of dictionaries
        """
        self.discounts = discounts
    
    def merge_line(self, line):
        u"""
        For transferring a line from another basket to this one.
        
        This is used with the "Saved" basket functionality.
        """
        try:
            existing_line = self.lines.get(line_reference=line.line_reference)
            
            # Line already exists - bump its quantity and delete the old
            existing_line.quantity += line.quantity
            existing_line.save()
            line.delete()
        except ObjectDoesNotExist:
            # Line does not already exist - reassign its basket
            line.basket = self
            line.save()
    
    def merge(self, basket):
        u"""Merges another basket with this one"""
        for line_to_merge in basket.all_lines():
            self.merge_line(line_to_merge)
        basket.status = MERGED
        basket.date_merged = datetime.datetime.now()
        basket.save()
    
    def set_as_submitted(self):
        u"""Mark this basket as submitted."""
        self.status = SUBMITTED
        self.date_submitted = datetime.datetime.now()
        self.save()
    
    # =======
    # Helpers
    # =======
    
    def _create_line_reference(self, item, options):
        u"""
        Returns a reference string for a line based on the item
        and its options.
        """
        if not options:
            return item.id
        return "%d_%s" % (item.id, zlib.crc32(str(options)))
    
    def _get_total(self, property):
        u"""
        For executing a named method on each line of the basket
        and returning the total.
        """
        total = Decimal('0.00')
        for line in self.all_lines():
            total += getattr(line, property)
        return total
    
    # ==========
    # Properties
    # ==========
    
    @property
    def is_empty(self):
        u"""Return bool based on basket having 0 lines"""
        return self.num_lines == 0
    
    @property
    def total_excl_tax(self):
        u"""Return total line price excluding tax"""
        return self._get_total('line_price_excl_tax_and_discounts')
    
    @property
    def total_tax(self):
        u"""Return total tax for a line"""
        return self._get_total('line_tax')
    
    @property
    def total_incl_tax(self):
        u"""Return total price for a line including tax"""
        return self._get_total('line_price_incl_tax_and_discounts')
    
    @property
    def num_lines(self):
        u"""Return number of lines"""
        return self.all_lines().count()
    
    @property
    def num_items(self):
        u"""Return number of items"""
        return reduce(lambda num,line: num+line.quantity, self.all_lines(), 0)
    
    @property
    def time_before_submit(self):
        if not self.date_submitted:
            return None
        return self.date_submitted - self.date_created
    
    @property
    def time_since_creation(self, test_datetime=None):
        if not test_datetime:
            test_datetime = datetime.datetime.now()
        return test_datetime - self.date_created
    
class AbstractLine(models.Model):
    u"""A line of a basket (product and a quantity)"""

    basket = models.ForeignKey('basket.Basket', related_name='lines')
    # This is to determine which products belong to the same line
    # We can't just use product.id as you can have customised products
    # which should be treated as separate lines.  Set as a 
    # SlugField as it is included in the path for certain views.
    line_reference = models.SlugField(max_length=128, db_index=True)
    
    product = models.ForeignKey('product.Item', related_name='basket_lines')
    quantity = models.PositiveIntegerField(default=1)
    
    # Instance variables used to persist discount information
    _discount_field = 'price_excl_tax'
    _discount = Decimal('0.00')
    _affected_quantity = 0
    
    class Meta:
        abstract = True
        unique_together = ("basket", "line_reference")
        
    def __unicode__(self):
        return u"%s, Product '%s', quantity %d" % (self.basket, self.product, self.quantity)
    
    def save(self, *args, **kwargs):
        u"""Saves a line or deletes if it's quanity is 0"""
        if self.quantity == 0:
            return self.delete(*args, **kwargs)
        super(AbstractLine, self).save(*args, **kwargs)

    # =============
    # Offer methods
    # =============
    
    def discount(self, discount_value, affected_quantity):
        self._discount += discount_value
        self._affected_quantity += affected_quantity
        
    def consume(self, quantity):
        self._affected_quantity += quantity
        
    def get_price_breakdown(self):
        u"""
        Returns a breakdown of line prices after discounts have 
        been applied.
        """
        prices = []
        if not self.has_discount:
            prices.append((self.unit_price_incl_tax, self.unit_price_excl_tax, self.quantity))
        else:
            # Need to split the discount among the affected quantity 
            # of products.
            item_incl_tax_discount = self._discount / self._affected_quantity
            item_excl_tax_discount = item_incl_tax_discount * self._tax_ratio
            prices.append((self.unit_price_incl_tax - item_incl_tax_discount, 
                           self.unit_price_excl_tax - item_excl_tax_discount,
                           self._affected_quantity))
            if self.quantity_without_discount:
                prices.append((self.unit_price_incl_tax, self.unit_price_excl_tax, self.quantity_without_discount))
        return prices

    # =======
    # Helpers
    # =======
    
    def _get_stockrecord_property(self, property):
        if not self.product.stockrecord:
            return None
        else:
            return getattr(self.product.stockrecord, property)
    
    @property
    def _tax_ratio(self):
        return self.unit_price_excl_tax / self.unit_price_incl_tax
    
    # ==========
    # Properties
    # ==========   
    
    @property
    def has_discount(self):
        return self.quantity > self.quantity_without_discount 
    
    @property
    def quantity_without_discount(self):
        return self.quantity - self._affected_quantity
    
    @property
    def discount_value(self):
        return self._discount
    
    @property
    def unit_price_excl_tax(self):
        u"""Return unit price excluding tax"""
        return self._get_stockrecord_property('price_excl_tax')
    
    @property
    def unit_tax(self):
        u"""Return tax of a unit"""
        return self._get_stockrecord_property('price_tax')
    
    @property
    def unit_price_incl_tax(self):
        u"""Return unit price including tax"""
        return self._get_stockrecord_property('price_incl_tax')
    
    @property
    def line_price_excl_tax(self):
        u"""Return line price excluding tax"""
        return self.quantity * self.unit_price_excl_tax
    
    @property
    def line_price_excl_tax_and_discounts(self):
        return self.line_price_excl_tax - self._discount * self._tax_ratio
    
    @property    
    def line_tax(self):
        u"""Return line tax"""
        return self.quantity * self.unit_tax
    
    @property
    def line_price_incl_tax(self):
        u"""Return line price including tax"""
        return self.quantity * self.unit_price_incl_tax
    
    @property
    def line_price_incl_tax_and_discounts(self):
        return self.line_price_incl_tax - self._discount
    
    @property
    def description(self):
        u"""Return product description"""
        d = str(self.product)
        ops = []
        for attribute in self.attributes.all():
            ops.append("%s = '%s'" % (attribute.option.name, attribute.value))
        if ops:
            d = "%s (%s)" % (d, ", ".join(ops))
        return d
    
    
class AbstractLineAttribute(models.Model):
    u"""An attribute of a basket line"""
    line = models.ForeignKey('basket.Line', related_name='attributes')
    option = models.ForeignKey('product.option')
    value = models.CharField(_("Value"), max_length=255)    
    
    class Meta:
        abstract = True
    

