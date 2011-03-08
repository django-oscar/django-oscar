from itertools import chain

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum

class AbstractOrder(models.Model):
    u"""An order"""
    number = models.CharField(_("Order number"), max_length=128, db_index=True)
    # We track the site that each order is placed within
    site = models.ForeignKey('sites.Site')
    basket = models.ForeignKey('basket.Basket')
    # Orders can be anonymous so we don't always have a customer ID
    user = models.ForeignKey(User, related_name='orders', null=True, blank=True)
    # Billing address is not always required (eg paying by gift card)
    billing_address = models.ForeignKey('order.BillingAddress', null=True, blank=True)
    # Total price looks like it could be calculated by adding up the
    # prices of the associated lines, but in some circumstances extra
    # order-level charges are added and so we need to store it separately
    total_incl_tax = models.DecimalField(_("Order total (inc. tax)"), decimal_places=2, max_digits=12)
    total_excl_tax = models.DecimalField(_("Order total (excl. tax)"), decimal_places=2, max_digits=12)
    
    # Shipping details
    shipping_incl_tax = models.DecimalField(_("Shipping charge (inc. tax)"), decimal_places=2, max_digits=12, default=0)
    shipping_excl_tax = models.DecimalField(_("Shipping charge (excl. tax)"), decimal_places=2, max_digits=12, default=0)
    # Not all lines are actually shipped (such as downloads)
    shipping_address = models.ForeignKey('order.ShippingAddress', null=True, blank=True)
    shipping_method = models.CharField(_("Shipping method"), max_length=128, null=True, blank=True)
    date_placed = models.DateTimeField(auto_now_add=True)
    
    @property
    def basket_total_incl_tax(self):
        u"""Return basket total including tax"""
        return self.total_incl_tax - self.shipping_incl_tax
    
    @property
    def basket_total_excl_tax(self):
        u"""Return basket total excluding tax"""
        return self.total_excl_tax - self.shipping_excl_tax
    
    @property
    def shipping_status(self):
        events = self.shipping_events.all()
        if not len(events):
            return ''
        
        # Collect all events by event-type
        map = {}
        for event in events:
            event_name = event.event_type.name
            if event_name not in map:
                map[event_name] = []
            map[event_name] = list(chain(map[event_name], event.line_quantities.all()))
        
        # Determine last complete event
        status = _("In progress")
        for event_name, event_line_quantities in map.items():
            if self._is_event_complete(event_line_quantities):
                status = event_name
        return status
    
    def _is_event_complete(self, event_quantites):
        # Form map of line to quantity
        map = {}
        for event_quantity in event_quantites:
            line_id = event_quantity.line_id
            map.setdefault(line_id, 0)
            map[line_id] += event_quantity.quantity
        
        for line in self.lines.all():
            if map[line.id] != line.quantity:
                return False
        return True
    
    class Meta:
        abstract = True
        ordering = ['-date_placed',]
    
    def __unicode__(self):
        return u"#%s" % (self.number,)


class AbstractOrderNote(models.Model):
    u"""A note against an order."""
    order = models.ForeignKey('order.Order', related_name="notes")
    user = models.ForeignKey('auth.User')
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"'%s' (%s)" % (self.message[0:50], self.user)


class AbstractCommunicationEvent(models.Model):
    u"""
    An order-level event involving a communication to the customer, such
    as an confirmation email being sent."""
    order = models.ForeignKey('order.Order', related_name="communication_events")
    type = models.ForeignKey('order.CommunicationEventType')
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    
class AbstractCommunicationEventType(models.Model):
    u"""Communication events are things like 'OrderConfirmationEmailSent'"""
    # Code is used in forms
    code = models.SlugField(max_length=128)
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
        
        
class AbstractLine(models.Model):
    u"""
    A order line (basically a product and a quantity)
    
    Not using a line model as it's difficult to capture and payment 
    information when it splits across a line.
    """
    order = models.ForeignKey('order.Order', related_name='lines')
    partner = models.ForeignKey('stock.Partner', related_name='order_lines')
    product = models.ForeignKey('product.Item')
    quantity = models.PositiveIntegerField(default=1)
    # Price information (these fields are actually redundant as the information
    # can be calculated from the LinePrice models
    line_price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    line_price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    
    # Partner information
    partner_reference = models.CharField(_("Partner reference"), max_length=128, blank=True, null=True,
        help_text=_("This is the item number that the partner uses within their system"))
    partner_notes = models.TextField(blank=True, null=True)
    
    @property
    def description(self):
        u"""
        Returns a description of this line including details of any 
        line attributes.
        """
        d = str(self.product)
        ops = []
        for attribute in self.attributes.all():
            ops.append("%s = '%s'" % (attribute.type, attribute.value))
        if ops:
            d = "%s (%s)" % (d, ", ".join(ops))
        return d
    
    @property
    def shipping_status(self):
        u"""Returns a string summary of the shipping status of this line"""
        status_map = self._shipping_event_history()
        if not status_map:
            return ''
        
        events = []    
        last_complete_event_name = None
        for event_dict in status_map:
            if event_dict['quantity'] == self.quantity:
                events.append(event_dict['name'])
                last_complete_event_name = event_dict['name']    
            else:
                events.append("%s (%d/%d items)" % (event_dict['name'], 
                                                    event_dict['quantity'], self.quantity))
        
        if last_complete_event_name == status_map[-1]['name']:
            return last_complete_event_name
            
        return ', '.join(events)
    
    def has_shipping_event_occurred(self, event_type):
        u"""Checks whether this line has passed a given shipping event"""
        for event_dict in self._shipping_event_history():
            if event_dict['name'] == event_type.name and event_dict['quantity'] == self.quantity:
                return True
        return False
    
    def _shipping_event_history(self):
        u"""
        Returns a list of shipping events"""
        status_map = {}
        for event in self.shippingevent_set.all():
            event_name = event.event_type.name
            event_quantity = event.line_quantities.get(line=self).quantity
            if event_name in status_map:
                status_map[event_name]['quantity'] += event_quantity
            else:
                status_map[event_name] = {'name': event_name, 'quantity': event_quantity}
        return list(status_map.values())
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Order lines")
        
    def __unicode__(self):
        return u"Product '%s', quantity '%s'" % (self.product, self.quantity)
    
    
class AbstractLineAttribute(models.Model):
    u"""An attribute of a line."""
    line = models.ForeignKey('order.Line', related_name='attributes')
    type = models.CharField(_("Type"), max_length=128)
    value = models.CharField(_("Value"), max_length=255)    
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return "%s = %s" % (self.type, self.value)
    
    
class AbstractLinePrice(models.Model):
    u"""
    For tracking the prices paid for each unit within a line.
    
    This is necessary as offers can lead to units within a line 
    having different prices.  For example, one product may be sold at
    50% off as it's part of an offer while the remainder are full price.
    """
    order = models.ForeignKey('order.Order', related_name='line_prices')
    line = models.ForeignKey('order.Line', related_name='prices')
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
    u"""
    An event is something which happens to a line such as
    payment being taken for 2 items, or 1 item being dispatched.
    """
    order = models.ForeignKey('order.Order', related_name='payment_events')
    line = models.ForeignKey('order.Line', related_name='payment_events')
    quantity = models.PositiveIntegerField(default=1)
    event_type = models.ForeignKey('order.PaymentEventType')
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Payment events")
        
    def __unicode__(self):
        return u"Order #%d, line %s: %d items %s" % (
            self.line.order.number, self.line.line_id, self.quantity, self.event_type)


class AbstractPaymentEventType(models.Model):
    u"""Payment events are things like 'Paid', 'Failed', 'Refunded'"""
    # Name is the friendly description of an event
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=128)
    # The normal order in which these shipping events take place
    sequence_number = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractPaymentEventType, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Payment event types")
        ordering = ('sequence_number',)
        
    def __unicode__(self):
        return self.name


class AbstractShippingEvent(models.Model):    
    u"""
    An event is something which happens to a group of lines such as
    1 item being dispatched.
    """
    order = models.ForeignKey('order.Order', related_name='shipping_events')
    lines = models.ManyToManyField('order.Line', through='ShippingEventQuantity')
    event_type = models.ForeignKey('order.ShippingEventType')
    notes = models.TextField(_("Event notes"), blank=True, null=True,
        help_text="This could be the dispatch reference, or a tracking number")
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Shipping events")
        ordering = ['-date']
        
    def __unicode__(self):
        return u"Order #%s, type %s" % (
            self.order.number, self.event_type)
        
    def num_affected_lines(self):
        return self.lines.count()


class ShippingEventQuantity(models.Model):
    u"""A "through" model linking lines to shipping events"""
    event = models.ForeignKey('order.ShippingEvent', related_name='line_quantities')
    line = models.ForeignKey('order.Line')
    quantity = models.PositiveIntegerField()

    def _check_previous_events_are_complete(self):
        u"""Checks whether previous shipping events have passed"""
        previous_events = ShippingEventQuantity.objects.filter(line=self.line, 
                                                               event__event_type__sequence_number__lt=self.event.event_type.sequence_number)
        self.quantity = int(self.quantity)
        for event_quantities in previous_events:
            if event_quantities.quantity < self.quantity:
                raise ValueError("Invalid quantity (%d) for event type (a previous event has not been fully passed)" % self.quantity)

    def _check_new_quantity(self):
        quantity_row = ShippingEventQuantity.objects.filter(line=self.line, 
                                                            event__event_type=self.event.event_type).aggregate(Sum('quantity'))
        previous_quantity = quantity_row['quantity__sum']
        if previous_quantity == None:
            previous_quantity = 0
        if previous_quantity + self.quantity > self.line.quantity:
            raise ValueError("Invalid quantity (%d) for event type (total exceeds line total)" % self.quantity)                                                        

    def save(self, *args, **kwargs):
        # Default quantity to full quantity of line
        if not self.quantity:
            self.quantity = self.line.quantity
        self._check_previous_events_are_complete()
        self._check_new_quantity()
        super(ShippingEventQuantity, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return "%s - quantity %d" % (self.line.product, self.quantity)


class AbstractShippingEventType(models.Model):
    u"""Shipping events are things like 'OrderPlaced', 'Acknowledged', 'Dispatched', 'Refunded'"""
    # Name is the friendly description of an event
    name = models.CharField(max_length=255)
    # Code is used in forms
    code = models.SlugField(max_length=128)
    is_required = models.BooleanField(default=True, help_text="This event must be passed before the next shipping event can take place")
    # The normal order in which these shipping events take place
    sequence_number = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractShippingEventType, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Shipping event types")
        ordering = ('sequence_number',)
        
    def __unicode__(self):
        return self.name
        
        

