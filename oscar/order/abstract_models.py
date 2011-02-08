from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _


class AbstractOrder(models.Model):
    """
    An order
    """
    number = models.PositiveIntegerField(_("Order number"), db_index=True)
    basket = models.ForeignKey('basket.Basket')
    # Orders can be anonymous so we don't always have a customer ID
    user = models.ForeignKey(User, related_name='orders', null=True, blank=True)
    # Billing address is not always required (eg paying by gift card)
    billing_address = models.ForeignKey('order.BillingAddress', null=True, blank=True)
    # Total price looks like it could be calculated by adding up the
    # prices of the associated batches, but in some circumstances extra
    # order-level charges are added and so we need to store it separately
    total_incl_tax = models.DecimalField(_("Order total (inc. tax)"), decimal_places=2, max_digits=12)
    total_excl_tax = models.DecimalField(_("Order total (excl. tax)"), decimal_places=2, max_digits=12)
    shipping_incl_tax = models.DecimalField(_("Shipping charge (inc. tax)"), decimal_places=2, max_digits=12, default=0)
    shipping_excl_tax = models.DecimalField(_("Shipping charge (excl. tax)"), decimal_places=2, max_digits=12, default=0)
    date_placed = models.DateTimeField(auto_now_add=True)
    
    def shipping_address(self):
        batches = self.batches.all()
        if len(batches) > 0:
            return batches[0].shipping_address
        return None
    
    @property
    def basket_total_incl_tax(self):
        return self.total_incl_tax - self.shipping_incl_tax
    
    @property
    def basket_total_excl_tax(self):
        return self.total_excl_tax - self.shipping_excl_tax
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number= self.basket.id
        super(AbstractOrder, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return u"#%s (amount: %.2f)" % (self.number, self.total_incl_tax)


class AbstractOrderNote(models.Model):
    """
    A note against an order.
    """
    order = models.ForeignKey('order.Order', related_name="notes")
    user = models.ForeignKey('auth.User')
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"'%s' (%s)" % (self.message[0:50], self.user)


class AbstractCommunicationEvent(models.Model):
    """
    An order-level event involving a communication to the customer, such
    as an confirmation email being sent.
    """
    order = models.ForeignKey('order.Order', related_name="events")
    type = models.ForeignKey('order.CommunicationEventType')
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    
class AbstractCommunicationEventType(models.Model):
    """ 
    Communication events are things like 'OrderConfirmationEmailSent'
    """
    # Code is used in forms
    code = models.CharField(max_length=128)
    # Name is the friendly description of an event
    name = models.CharField(max_length=255)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractOrderEventType, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Communication event types")
        
    def __unicode__(self):
        return self.name    
    

class AbstractBatch(models.Model):
    """
    A batch of items from a single fulfillment partner
    
    This is a set of order lines which are fulfilled by a single partner
    """
    order = models.ForeignKey('order.Order', related_name="batches")
    partner = models.ForeignKey('stock.Partner')
    # Not all batches are actually shipped (such as downloads)
    shipping_address = models.ForeignKey('order.ShippingAddress', null=True, blank=True)
    shipping_method = models.CharField(_("Shipping method"), max_length=128, null=True, blank=True)
    
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
    order = models.ForeignKey('order.Order', related_name='lines')
    batch = models.ForeignKey('order.Batch', related_name='lines')
    product = models.ForeignKey('product.Item')
    quantity = models.PositiveIntegerField(default=1)
    # Price information (these fields are actually redundant as the information
    # can be calculated from the BatchLinePrice models
    line_price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    line_price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    
    # Partner information
    partner_reference = models.CharField(_("Partner reference"), max_length=128, blank=True, null=True,
        help_text=_("This is the item number that the partner uses within their system"))
    partner_notes = models.TextField(blank=True, null=True)
    
    @property
    def description(self):
        d = str(self.product)
        ops = []
        for attribute in self.attributes.all():
            ops.append("%s = '%s'" % (attribute.type, attribute.value))
        if ops:
            d = "%s (%s)" % (d, ", ".join(ops))
        return d
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Batch lines")
        
    def __unicode__(self):
        return u"Product '%s', quantity '%s'" % (self.product, self.quantity)
    
    
class AbstractBatchLineAttribute(models.Model):
    """
    An attribute of a batch line.
    """
    line = models.ForeignKey('order.BatchLine', related_name='attributes')
    type = models.CharField(_("Type"), max_length=128)
    value = models.CharField(_("Value"), max_length=255)    
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return "%s = %s" % (self.type, self.value)
    
    
class AbstractBatchLinePrice(models.Model):
    """
    For tracking the prices paid for each unit within a line.
    
    This is necessary as offers can lead to units within a line 
    having different prices.  For example, one product may be sold at
    50% off as it's part of an offer while the remainder are full price.
    """
    order = models.ForeignKey('order.Order', related_name='line_prices')
    line = models.ForeignKey('order.BatchLine', related_name='prices')
    quantity = models.PositiveIntegerField(default=1)
    price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    shipping_incl_tax = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    shipping_excl_tax = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"Line '%s' (quantity %d) price %s" % (self.line, self.quantity, self.price_incl_tax)
   
   
class AbstractPaymentEvent(models.Model):    
    """
    An event is something which happens to a line such as
    payment being taken for 2 items, or 1 item being dispatched.
    """
    order = models.ForeignKey('order.Order', related_name='payment_events')
    line = models.ForeignKey('order.BatchLine', related_name='payment_events')
    quantity = models.PositiveIntegerField(default=1)
    event_type = models.ForeignKey('order.PaymentEventType')
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Payment events")
        
    def __unicode__(self):
        return u"Order #%d, batch #%d, line %s: %d items %s" % (
            self.line.batch.order.number, self.line.batch.id, self.line.line_id, self.quantity, self.event_type)


class AbstractPaymentEventType(models.Model):
    """ 
    Payment events are things like 'Paid', 'Failed', 'Refunded'
    """
    # Code is used in forms
    code = models.CharField(max_length=128)
    # Name is the friendly description of an event
    name = models.CharField(max_length=255)
    # The normal order in which these shipping events take place
    order = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractPaymentEventType, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Payment event types")
        ordering = ('order',)
        
    def __unicode__(self):
        return self.name


class AbstractShippingEvent(models.Model):    
    """
    An event is something which happens to a group of lines such as
    1 item being dispatched.
    """
    order = models.ForeignKey('order.Order', related_name='shipping_events')
    batch = models.ForeignKey('order.Batch', related_name='shipping_events')
    lines = models.ManyToManyField('order.BatchLine', through='ShippingEventQuantity')
    event_type = models.ForeignKey('order.ShippingEventType')
    notes = models.TextField(_("Event notes"), blank=True, null=True,
        help_text="This could be the dispatch reference, or a tracking number")
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Shipping events")
        
    def __unicode__(self):
        return u"Order #%d, line %s: %d items set to '%s'" % (
            self.order.number, self.line.id, self.quantity, self.event_type)
        
    def num_affected_lines(self):
        return self.lines.count()


class ShippingEventQuantity(models.Model):
    event = models.ForeignKey('order.ShippingEvent')
    line = models.ForeignKey('order.BatchLine')
    quantity = models.PositiveIntegerField()


class AbstractShippingEventType(models.Model):
    """ 
    Shipping events are things like 'OrderPlaced', 'Acknowledged', 'Dispatched', 'Refunded'
    """
    # Code is used in forms
    code = models.CharField(max_length=128)
    # Name is the friendly description of an event
    name = models.CharField(max_length=255)
    # The normal order in which these shipping events take place
    order = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractShippingEventType, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Shipping event types")
        ordering = ('order',)
        
    def __unicode__(self):
        return self.name
        
        

