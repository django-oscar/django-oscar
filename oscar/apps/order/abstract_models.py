from itertools import chain
from decimal import Decimal as D

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist


class AbstractOrder(models.Model):
    """
    The main order model
    """
    
    number = models.CharField(_("Order number"), max_length=128, db_index=True)
    # We track the site that each order is placed within
    site = models.ForeignKey('sites.Site')
    basket = models.ForeignKey('basket.Basket', null=True, blank=True)
    # Orders can be anonymous so we don't always have a customer ID
    user = models.ForeignKey(User, related_name='orders', null=True, blank=True)
    # Billing address is not always required (eg paying by gift card)
    billing_address = models.ForeignKey('order.BillingAddress', null=True, blank=True)
    
    # Total price looks like it could be calculated by adding up the
    # prices of the associated lines, but in some circumstances extra
    # order-level charges are added and so we need to store it separately
    total_incl_tax = models.DecimalField(_("Order total (inc. tax)"), decimal_places=2, max_digits=12)
    total_excl_tax = models.DecimalField(_("Order total (excl. tax)"), decimal_places=2, max_digits=12)
    
    # Shipping charges
    shipping_incl_tax = models.DecimalField(_("Shipping charge (inc. tax)"), decimal_places=2, max_digits=12, default=0)
    shipping_excl_tax = models.DecimalField(_("Shipping charge (excl. tax)"), decimal_places=2, max_digits=12, default=0)
    
    # Not all lines are actually shipped (such as downloads), hence shipping address
    # is not mandatory.
    shipping_address = models.ForeignKey('order.ShippingAddress', null=True, blank=True)
    shipping_method = models.CharField(_("Shipping method"), max_length=128, null=True, blank=True)
    
    # Use this field to indicate that an order is on hold / awaiting payment
    status = models.CharField(_("Status"), max_length=100, null=True, blank=True)
    
    # Index added to this field for reporting
    date_placed = models.DateTimeField(auto_now_add=True, db_index=True)
    
    @property
    def basket_total_incl_tax(self):
        """
        Return basket total including tax
        """
        return self.total_incl_tax - self.shipping_incl_tax
    
    @property
    def basket_total_excl_tax(self):
        """
        Return basket total excluding tax
        """
        return self.total_excl_tax - self.shipping_excl_tax
    
    @property
    def total_before_discounts_incl_tax(self):
        total = D('0.00')
        for line in self.lines.all():
            total += line.line_price_before_discounts_incl_tax
        total += self.shipping_incl_tax
        return total
    
    @property
    def total_before_discounts_excl_tax(self):
        total = D('0.00')
        for line in self.lines.all():
            total += line.line_price_before_discounts_excl_tax
        total += self.shipping_excl_tax
        return total
    
    @property
    def total_discount_incl_tax(self):
        """
        The amount of discount this order received
        """
        discount = D('0.00')
        for line in self.lines.all():
            discount += line.discount_incl_tax
        return discount
    
    @property
    def total_discount_excl_tax(self):
        discount = D('0.00')
        for line in self.lines.all():
            discount += line.discount_excl_tax
        return discount
    
    @property
    def total_tax(self):
        return self.total_incl_tax - self.total_excl_tax
    
    @property
    def num_lines(self):
        return self.lines.count()
    
    @property
    def num_items(self):
        u"""
        Returns the number of items in this order.
        """
        num_items = 0
        for line in self.lines.all():
            num_items += line.quantity
        return num_items
    
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
        permissions = (
            ("can_view", "Can view orders (eg for reporting)"),
        )
    
    def __unicode__(self):
        return u"#%s" % (self.number,)


class AbstractOrderNote(models.Model):
    """
    A note against an order.
    
    This are often used for audit purposes too.  IE, whenever an admin
    makes a change to an order, we create a note to record what happened.
    """
    order = models.ForeignKey('order.Order', related_name="notes")
    
    # These are sometimes programatically generated so don't need a 
    # user everytime
    user = models.ForeignKey('auth.User', null=True)
    
    # We allow notes to be classified although this isn't always needed
    INFO, WARNING, ERROR = 'Info', 'Warning', 'Error'
    note_type = models.CharField(max_length=128, null=True)
    
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
    order = models.ForeignKey('order.Order', related_name="communication_events")
    type = models.ForeignKey('customer.CommunicationEventType')
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"'%s' event for order #%s" % (self.type.name, self.order.number)
    
        
class AbstractLine(models.Model):
    """
    A order line (basically a product and a quantity)
    
    Not using a line model as it's difficult to capture and payment 
    information when it splits across a line.
    """
    order = models.ForeignKey('order.Order', related_name='lines')
    
    # We store the partner, their SKU and the title for cases where the product has been
    # deleted from the catalogue.  We also store the partner name in case the partner
    # gets deleted at a later date.
    partner = models.ForeignKey('partner.Partner', related_name='order_lines', blank=True, null=True, on_delete=models.SET_NULL)
    partner_name = models.CharField(_("Partner name"), max_length=128)
    partner_sku = models.CharField(_("Partner SKU"), max_length=128)
    title = models.CharField(_("Title"), max_length=255)
    
    # We don't want any hard links between orders and the products table so we allow
    # this link to be NULLable.
    product = models.ForeignKey('catalogue.Product', on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # Price information (these fields are actually redundant as the information
    # can be calculated from the LinePrice models
    line_price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    line_price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    
    # Price information before discounts are applied
    line_price_before_discounts_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    line_price_before_discounts_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)

    # REPORTING FIELDS        
    # Cost price (the price charged by the fulfilment partner for this product).
    unit_cost_price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    # Normal site price for item (without discounts)
    unit_price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    unit_price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    # Retail price at time of purchase
    unit_retail_price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    
    # Partner information
    partner_line_reference = models.CharField(_("Partner reference"), max_length=128, blank=True, null=True,
        help_text=_("This is the item number that the partner uses within their system"))
    partner_line_notes = models.TextField(blank=True, null=True)
    
    # Partners often want to assign some status to each line to help with their own 
    # business processes.
    status = models.CharField(_("Status"), max_length=255, null=True, blank=True)
    
    # Estimated dispatch date - should be set at order time
    est_dispatch_date = models.DateField(blank=True, null=True)
    
    @property
    def description(self):
        """
        Returns a description of this line including details of any 
        line attributes.
        """
        desc = self.title
        ops = []
        for attribute in self.attributes.all():
            ops.append("%s = '%s'" % (attribute.type, attribute.value))
        if ops:
            desc = "%s (%s)" % (desc, ", ".join(ops))
        return desc
    
    @property
    def discount_incl_tax(self):
        return self.line_price_before_discounts_incl_tax - self.line_price_incl_tax
    
    @property
    def discount_excl_tax(self):
        return self.line_price_before_discounts_excl_tax - self.line_price_excl_tax
    
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
    
    @property
    def is_product_deleted(self):
        return self.product == None
    
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
        if self.product:
            title = self.product.title
        else:
            title = '<missing product>'
        return u"Product '%s', quantity '%s'" % (title, self.quantity)
    
    
class AbstractLineAttribute(models.Model):
    u"""An attribute of a line."""
    line = models.ForeignKey('order.Line', related_name='attributes')
    option = models.ForeignKey('catalogue.Option', null=True, on_delete=models.SET_NULL, related_name="line_attributes")
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
   
   
# PAYMENT EVENTS   


class AbstractPaymentEventType(models.Model):
    """
    Payment events are things like 'Paid', 'Failed', 'Refunded'
    """
    name = models.CharField(max_length=128)
    code = models.SlugField(max_length=128)
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
   
   
class AbstractPaymentEvent(models.Model):    
    """
    An event is something which happens to a line such as
    payment being taken for 2 items, or 1 item being dispatched.
    """
    order = models.ForeignKey('order.Order', related_name='payment_events')
    lines = models.ManyToManyField('order.Line', through='PaymentEventQuantity')
    event_type = models.ForeignKey('order.PaymentEventType')
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = _("Payment events")
        
    def __unicode__(self):
        return u"Payment event for order #%d" % self.order


class PaymentEventQuantity(models.Model):
    """
    A "through" model linking lines to payment events
    """
    event = models.ForeignKey('order.PaymentEvent', related_name='line_quantities')
    line = models.ForeignKey('order.Line')
    quantity = models.PositiveIntegerField()


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
        previous_events = ShippingEventQuantity._default_manager.filter(line=self.line, 
                                                                        event__event_type__sequence_number__lt=self.event.event_type.sequence_number)
        self.quantity = int(self.quantity)
        for event_quantities in previous_events:
            if event_quantities.quantity < self.quantity:
                raise ValueError("Invalid quantity (%d) for event type (a previous event has not been fully passed)" % self.quantity)

    def _check_new_quantity(self):
        quantity_row = ShippingEventQuantity._default_manager.filter(line=self.line, 
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
    # Code is used in forms
    code = models.CharField(max_length=128)
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
        
        
class AbstractOrderDiscount(models.Model):
    """
    A discount against an order.
    
    Normally only used for display purposes so an order can be listed with discounts displayed
    separately even though in reality, the discounts are applied at the line level.
    """
    order = models.ForeignKey('order.Order', related_name="discounts")
    offer = models.ForeignKey('offer.ConditionalOffer', null=True, on_delete=models.SET_NULL)
    voucher = models.ForeignKey('voucher.Voucher', related_name="discount_vouchers", null=True, on_delete=models.SET_NULL)
    voucher_code = models.CharField(_("Code"), max_length=128, db_index=True, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"Discount of %r from order %s" % (self.amount, self.order)    
        
    def description(self):
        if self.voucher_code:
            return self.voucher_code
        return self.offer.name
