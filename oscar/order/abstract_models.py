from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class AbstractOrder(models.Model):
    """
    An order
    """
    number = models.IntegerField(_("Order number"))
    basket = models.ForeignKey('basket.Basket')
    customer = models.ForeignKey(User, related_name='orders')
    billing_address = models.ForeignKey('order.BillingAddress')
    # Total price looks like it could be calculated by adding up the
    # prices of the associated batches, but in some circumstances extra
    # order-level charges are added and so we need to store it separately
    total_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    total_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    delivery_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    delivery_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    date_placed = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return "#%d (customer: %s, amount: %.2f)" % (self.number, self.customer.username, self.total_incl_tax)

class AbstractBatch(models.Model):
    """
    A batch of items from a single fulfillment partner
    
    This is a set of order lines which are fulfilled by a single partner
    """
    order = models.ForeignKey('order.Order')
    partner = models.ForeignKey('stock.Partner')
    delivery_method = models.CharField(_("Delivery method"), max_length=128)
    # Not all batches are actually delivered (such as downloads)
    delivery_address = models.ForeignKey('order.DeliveryAddress', null=True, blank=True)
    # Whether the batch should be dispatched in one go, or as they become available
    dispatch_option = models.CharField(max_length=128, null=True, blank=True)
    
    def get_num_items(self):
        return len(self.lines.all())
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Batches")
    
    def __unicode__(self):
        return "%s batch for order #%d" % (self.partner.name, self.order.number)
        
class AbstractBatchLine(models.Model):
    """
    A line within a batch.
    
    Not using a line model as it's difficult to capture and payment 
    information when it splits across a line.
    """
    batch = models.ForeignKey('order.Batch', related_name='lines')
    product = models.ForeignKey('product.Item')
    quantity = models.PositiveIntegerField(default=1)
    # Price information (these fields are actually redundant as the information
    # can be calculated from the BatchLinePrice models
    line_price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    line_price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    
    # Partner information
    partner_reference = models.CharField(max_length=128, blank=True, null=True,
        help_text=_("This is the item number that the partner uses within their system"))
    partner_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Batch lines")
        
    def __unicode__(self):
        return "Product '%s', quantity '%s'" % (self.product, self.quantity)
    
class AbstractBatchLinePrice(models.Model):
    """
    For tracking the prices paid for each unit within a line.
    
    This is necessary as offers can lead to units within a line 
    having different prices.  For example, one product may be sold at
    50% off as it's part of an offer while the remainder are full price.
    """
    line = models.ForeignKey('order.BatchLine', related_name='prices')
    quantity = models.PositiveIntegerField(default=1)
    price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    delivery_incl_tax = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    delivery_excl_tax = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    
class AbstractBatchLineEvent(models.Model):    
    """
    An event is something which happens to a line such as
    payment being taken for 2 items, or 1 item being dispatched.
    """
    line = models.ForeignKey('order.BatchLine', related_name='events')
    quantity = models.PositiveIntegerField(default=1)
    event_type = models.ForeignKey('order.BatchLineEventType')
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Batch line events")
        
    def __unicode__(self):
        return "Order #%d, batch #%d, line %s: %d items %s" % (
            self.line.batch.order.number, self.line.batch.id, self.line.line_id, self.quantity, self.event_type)

class AbstractBatchLineEventType(models.Model):
    """ 
    Event types: eg Paid, Cancelled, Dispatched, Returned
    """
    name = models.CharField(max_length=128)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Batch line event types")
        
    def __unicode__(self):
        return self.name
        
class AbstractBatchLineAttribute(models.Model):
    """
    An attribute of a batch line.
    """
    line = models.ForeignKey('order.BatchLine', related_name='attributes')
    type = models.CharField(max_length=128)
    value = models.CharField(max_length=255)    
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return "%s = %s" % (self.type, self.value)
