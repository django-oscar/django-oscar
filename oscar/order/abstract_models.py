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
    # Totals
    total_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    delivery_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
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
    
    def num_items(self):
        return len(self.items.all())
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Batches")
    
    def __unicode__(self):
        return "%s batch for order #%d" % (self.partner.name, self.order.number)
        
class AbstractBatchItem(models.Model):
    """
    A item within a batch.
    
    Not using a line model as it's difficult to capture and payment 
    information when it splits across a line.
    """
    batch = models.ForeignKey('order.Batch', related_name='items')
    # As all order items are stored in their own row, this ID is used to 
    # determine which are part of the same line.
    line_id = models.CharField(max_length=128)
    product = models.ForeignKey('product.Item')
    # Partner information
    partner_reference = models.CharField(max_length=128, blank=True, null=True,
        help_text=_("This is the item number that the partner uses within their system"))
    partner_notes = models.TextField(blank=True, null=True)
    # Price information
    price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    delivery_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    delivery_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    # Payment status
    OUTSTANDING, PAID, FAILED = ('Outstanding', 'Paid', 'Failed')
    PAYMENT_CHOICES = (
        (OUTSTANDING, _("Not paid for yet")),
        (PAID, _("Payment received")),
        (FAILED, _("Payment failed")),
    )
    payment_status = models.CharField(max_length=255, 
        choices=PAYMENT_CHOICES, 
        default=OUTSTANDING)
    # Shipping status
    # @todo Make this set of choices configurable per project
    ON_HOLD, PENDING_SUBMISSION, SUBMITTED, ACKNOWLEDGED, DISPATCHED, RETURNED = (
        'On hold',
        'Pending submission',
        'Submitted',
        'Acknowledged',
        'Dispatched',
        'Returned'
    )
    SHIPPING_CHOICES = (
        (ON_HOLD, _("On hold")),
        (PENDING_SUBMISSION, _("Pending submission")),
        (SUBMITTED, _("Submitted")),
        (ACKNOWLEDGED, _("Acknowledged by partner")),
        (DISPATCHED, _("Dispatched")),
        (RETURNED, _("Returned")),
    )
    shipping_status = models.CharField(max_length=255, choices=SHIPPING_CHOICES, default=PENDING_SUBMISSION)
    # Various dates
    date_paid = models.DateTimeField(blank=True, null=True)
    date_cancelled = models.DateTimeField(blank=True, null=True)
    date_dispatched = models.DateField(blank=True, null=True)
    date_returned = models.DateTimeField(blank=True, null=True)
    date_refunded = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Batch items")
        
class AbstractBatchItemAttribute(models.Model):
    """
    An attribute of a batch item.
    """
    batch_item = models.ForeignKey('order.BatchItem', related_name='attributes')
    type = models.CharField(max_length=128)
    value = models.CharField(max_length=255)    
    
    class Meta:
        abstract = True
