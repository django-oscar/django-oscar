from itertools import chain
from decimal import Decimal as D
import hashlib
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum
from django.conf import settings

from oscar.apps.order.exceptions import (InvalidOrderStatus, InvalidLineStatus,
                                         InvalidShippingEvent)


class AbstractOrder(models.Model):
    """
    The main order model
    """
    number = models.CharField(_("Order number"), max_length=128, db_index=True)
    # We track the site that each order is placed within
    site = models.ForeignKey('sites.Site')
    basket_id = models.PositiveIntegerField(_('Basket ID'), null=True, blank=True)
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

    guest_email = models.EmailField(_("Guest email address"), null=True, blank=True)

    # Index added to this field for reporting
    date_placed = models.DateTimeField(auto_now_add=True, db_index=True)

    # Dict of available status changes
    pipeline = getattr(settings,  'OSCAR_ORDER_STATUS_PIPELINE', {})
    cascade = getattr(settings,  'OSCAR_ORDER_STATUS_CASCADE', {})

    @classmethod
    def all_statuses(cls):
        return cls.pipeline.keys()

    def available_statuses(self):
        return self.pipeline.get(self.status, ())

    def set_status(self, new_status):
        if new_status == self.status:
            return
        if new_status not in self.available_statuses():
            raise InvalidOrderStatus(_("'%(new_status)s' is not a valid status for order %(number)s "+
                                       "(current status: '%(status)s')") % {
                                            'new_status': new_status,
                                            'number': self.number,
                                            'status': self.status})
        self.status = new_status
        if new_status in self.cascade:
            for line in self.lines.all():
                line.status = self.cascade[self.status]
                line.save()
        self.save()

    @property
    def is_anonymous(self):
        return self.user is None

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
        """
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
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")


    def __unicode__(self):
        return u"#%s" % (self.number,)

    def verification_hash(self):
        return hashlib.md5('%s%s' % (self.number, settings.SECRET_KEY)).hexdigest()

    @property
    def email(self):
        if not self.user:
            return self.guest_email
        return self.user.email


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
    INFO, WARNING, ERROR, SYSTEM = 'Info', 'Warning', 'Error', 'System'
    note_type = models.CharField(_('Note Type'), max_length=128, null=True)

    message = models.TextField(_('Message'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Notes can only be edited for 5 minutes after being created
    editable_lifetime = 300

    class Meta:
        abstract = True
        verbose_name = _("Order Note")
        verbose_name_plural = _("Order Notes")

    def __unicode__(self):
        return u"'%s' (%s)" % (self.message[0:50], self.user)

    def is_editable(self):
        if self.note_type == self.SYSTEM:
            return False
        return (datetime.datetime.now() - self.date_updated).seconds < self.editable_lifetime


class AbstractCommunicationEvent(models.Model):
    """
    An order-level event involving a communication to the customer, such
    as an confirmation email being sent.
    """
    order = models.ForeignKey('order.Order', related_name="communication_events")
    event_type = models.ForeignKey('customer.CommunicationEventType')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Communication Event")
        verbose_name_plural = _("Communication Events")

    def __unicode__(self):
        return _("'%(type)s' event for order #%(number)s") % {'type': self.type.name, 'number': self.order.number}


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
    upc = models.CharField(_("UPC"), max_length=128, blank=True, null=True)

    # We don't want any hard links between orders and the products table so we allow
    # this link to be NULLable.
    product = models.ForeignKey('catalogue.Product', on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)

    # Price information (these fields are actually redundant as the information
    # can be calculated from the LinePrice models
    line_price_incl_tax = models.DecimalField(_('Price (inc. tax)'), decimal_places=2, max_digits=12)
    line_price_excl_tax = models.DecimalField(_('Price (excl. tax)'), decimal_places=2, max_digits=12)

    # Price information before discounts are applied
    line_price_before_discounts_incl_tax = models.DecimalField(_('Price before discounts (inc. tax)'),
        decimal_places=2, max_digits=12)
    line_price_before_discounts_excl_tax = models.DecimalField(_('Price before discounts (excl. tax)'),
        decimal_places=2, max_digits=12)

    # REPORTING FIELDS
    # Cost price (the price charged by the fulfilment partner for this product).
    unit_cost_price = models.DecimalField(_('Unit Cost Price'), decimal_places=2, max_digits=12, blank=True, null=True)
    # Normal site price for item (without discounts)
    unit_price_incl_tax = models.DecimalField(_('Unit Price (inc. tax)'),decimal_places=2, max_digits=12,
        blank=True, null=True)
    unit_price_excl_tax = models.DecimalField(_('Unit Price (excl. tax)'), decimal_places=2, max_digits=12,
        blank=True, null=True)
    # Retail price at time of purchase
    unit_retail_price = models.DecimalField(_('Unit Retail Price'), decimal_places=2, max_digits=12,
        blank=True, null=True)

    # Partner information
    partner_line_reference = models.CharField(_("Partner reference"), max_length=128, blank=True, null=True,
        help_text=_("This is the item number that the partner uses within their system"))
    partner_line_notes = models.TextField(_('Partner Notes'), blank=True, null=True)

    # Partners often want to assign some status to each line to help with their own
    # business processes.
    status = models.CharField(_("Status"), max_length=255, null=True, blank=True)

    # Estimated dispatch date - should be set at order time
    est_dispatch_date = models.DateField(_('Estimated Dispatch Date'), blank=True, null=True)

    pipeline = getattr(settings,  'OSCAR_LINE_STATUS_PIPELINE', {})

    @classmethod
    def all_statuses(cls):
        return cls.pipeline.keys()

    def available_statuses(self):
        return self.pipeline.get(self.status, ())

    def set_status(self, new_status):
        if new_status == self.status:
            return
        if new_status not in self.available_statuses():
            raise InvalidLineStatus(_("'%(new_status)s' is not a valid status (current status: '%(status)s')") % {
                                    'new_status': new_status, 'status': self.status})
        self.status = new_status
        self.save()

    @property
    def category(self):
        """
        Used by Google analytics tracking
        """
        return None

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
    def line_price_tax(self):
        return self.line_price_incl_tax - self.line_price_excl_tax

    @property
    def unit_price_tax(self):
        return self.unit_price_incl_tax - self.unit_price_excl_tax

    @property
    def shipping_status(self):
        """Returns a string summary of the shipping status of this line"""
        status_map = self.shipping_event_breakdown()
        if not status_map:
            return ''

        events = []
        last_complete_event_name = None
        for event_dict in status_map.values():
            if event_dict['quantity'] == self.quantity:
                events.append(event_dict['name'])
                last_complete_event_name = event_dict['name']
            else:
                events.append("%s (%d/%d items)" % (event_dict['name'],
                                                    event_dict['quantity'], self.quantity))

        if last_complete_event_name == status_map.values()[-1]['name']:
            return last_complete_event_name

        return ', '.join(events)

    def has_shipping_event_occurred(self, event_type, quantity=None):
        """
        Check whether this line has passed a given shipping event
        """
        if not quantity:
            quantity = self.quantity
        for name, event_dict in self.shipping_event_breakdown().items():
            if name == event_type.name and event_dict['quantity'] == self.quantity:
                return True
        return False

    @property
    def is_product_deleted(self):
        return self.product == None

    def shipping_event_breakdown(self):
        """
        Returns a dict of shipping events that this line has been through
        """
        status_map = {}
        for event in self.shippingevent_set.all():
            event_type = event.event_type
            event_name = event_type.name
            event_quantity = event.line_quantities.get(line=self).quantity
            if event_name in status_map:
                status_map[event_name]['quantity'] += event_quantity
            else:
                status_map[event_name] = {'name': event_name,
                                          'event_type': event.event_type,
                                          'quantity': event_quantity}
        return status_map

    class Meta:
        abstract = True
        verbose_name = _("Order line")
        verbose_name_plural = _("Order lines")

    def __unicode__(self):
        if self.product:
            title = self.product.title
        else:
            title = _('<missing product>')
        return _("Product '%(name)s', quantity '%(qty)s'") % {'name': title, 'qty': self.quantity}


class AbstractLineAttribute(models.Model):
    u"""An attribute of a line."""
    line = models.ForeignKey('order.Line', related_name='attributes')
    option = models.ForeignKey('catalogue.Option', null=True, on_delete=models.SET_NULL, related_name="line_attributes")
    type = models.CharField(_("Type"), max_length=128)
    value = models.CharField(_("Value"), max_length=255)

    class Meta:
        abstract = True
        verbose_name = _("Line Attribute")
        verbose_name_plural = _("Line Attributes")

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
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)
    price_incl_tax = models.DecimalField(_('Price (inc. tax)'), decimal_places=2, max_digits=12)
    price_excl_tax = models.DecimalField(_('Price (excl. tax)'), decimal_places=2, max_digits=12)
    shipping_incl_tax = models.DecimalField(_('Shiping (inc. tax)'), decimal_places=2, max_digits=12, default=0)
    shipping_excl_tax = models.DecimalField(_('Shipping (excl. tax)'), decimal_places=2, max_digits=12, default=0)

    class Meta:
        abstract = True
        ordering = ('id',)
        verbose_name = _("Line Price")
        verbose_name_plural = _("Line Prices")

    def __unicode__(self):
        return _("Line '%(number)s' (quantity %(qty)d) price %(price)s") % {
            'number': self.line, 'qty': self.quantity, 'price': self.price_incl_tax}


# PAYMENT EVENTS


class AbstractPaymentEventType(models.Model):
    """
    Payment events are things like 'Paid', 'Failed', 'Refunded'
    """
    name = models.CharField(_('Name'), max_length=128, unique=True)
    code = models.SlugField(_('Code'), max_length=128, unique=True)
    sequence_number = models.PositiveIntegerField(_('Sequence'), default=0)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractPaymentEventType, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        verbose_name = _("Payment event type")
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
    amount = models.DecimalField(_('Amount'), decimal_places=2, max_digits=12)
    lines = models.ManyToManyField('order.Line', through='PaymentEventQuantity')
    event_type = models.ForeignKey('order.PaymentEventType')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Payment event")
        verbose_name_plural = _("Payment events")

    def __unicode__(self):
        return _("Payment event for order %s") % self.order


class PaymentEventQuantity(models.Model):
    """
    A "through" model linking lines to payment events
    """
    event = models.ForeignKey('order.PaymentEvent', related_name='line_quantities')
    line = models.ForeignKey('order.Line')
    quantity = models.PositiveIntegerField(_('Quantity'))

    class Meta:
        verbose_name = _("Payment Event Quantity")
        verbose_name_plural = _("Payment Event Quantities")


# SHIPPING EVENTS


class AbstractShippingEvent(models.Model):
    """
    An event is something which happens to a group of lines such as
    1 item being dispatched.
    """
    order = models.ForeignKey('order.Order', related_name='shipping_events')
    lines = models.ManyToManyField('order.Line', through='ShippingEventQuantity')
    event_type = models.ForeignKey('order.ShippingEventType')
    notes = models.TextField(_("Event notes"), blank=True, null=True,
        help_text=_("This could be the dispatch reference, or a tracking number"))
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Shipping event")
        verbose_name_plural = _("Shipping events")
        ordering = ['-date']

    def __unicode__(self):
        return _("Order #%(number)s, type %(type)s") % {
                'number': self.order.number, 'type': self.event_type}

    def num_affected_lines(self):
        return self.lines.count()


class ShippingEventQuantity(models.Model):
    """
    A "through" model linking lines to shipping events
    """
    event = models.ForeignKey('order.ShippingEvent', related_name='line_quantities')
    line = models.ForeignKey('order.Line')
    quantity = models.PositiveIntegerField(_('Quantity'))

    class Meta:
        verbose_name = _("Shipping Event Quantity")
        verbose_name_plural = _("Shipping Event Quantities")

    def _check_previous_events_are_complete(self):
        """
        Checks whether previous shipping events have passed
        """
        # Quantity of the proposd event must have occurred for
        # the previous events in the sequence.
        previous_event_types = self.event.event_type.get_prerequisites()
        for event_type in previous_event_types:
            quantity = ShippingEventQuantity._default_manager.filter(
                line=self.line,
                event__event_type=event_type).aggregate(Sum('quantity'))['quantity__sum']
            if quantity is None or quantity < int(self.quantity):
                raise InvalidShippingEvent(_("This shipping event is not permitted"))

    def _check_new_quantity(self):
        quantity_row = ShippingEventQuantity._default_manager.filter(line=self.line,
                                                                     event__event_type=self.event.event_type).aggregate(Sum('quantity'))
        previous_quantity = quantity_row['quantity__sum']
        if previous_quantity == None:
            previous_quantity = 0
        if previous_quantity + self.quantity > self.line.quantity:
            raise ValueError(_("Invalid quantity (%d) for event type (total exceeds line total)") % self.quantity)

    def save(self, *args, **kwargs):
        # Default quantity to full quantity of line
        if not self.quantity:
            self.quantity = self.line.quantity
        self.quantity = int(self.quantity)
        self._check_previous_events_are_complete()
        self._check_new_quantity()
        super(ShippingEventQuantity, self).save(*args, **kwargs)

    def __unicode__(self):
        return _(u"%(product)s - quantity %(qty)d") % {'product': self.line.product, 'qty': self.quantity}


class AbstractShippingEventType(models.Model):
    """
    Shipping events are things like 'OrderPlaced', 'Acknowledged', 'Dispatched', 'Refunded'
    """
    # Name is the friendly description of an event
    name = models.CharField(_('Name'), max_length=255, unique=True)
    # Code is used in forms
    code = models.SlugField(_('Code'), max_length=128, unique=True)
    is_required = models.BooleanField(_('Is Required'), default=True,
        help_text=_("This event must be passed before the next shipping event can take place"))
    # The normal order in which these shipping events take place
    sequence_number = models.PositiveIntegerField(_('Sequence'), default=0)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractShippingEventType, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        verbose_name = _("Shipping event type")
        verbose_name_plural = _("Shipping event types")
        ordering = ('sequence_number',)

    def __unicode__(self):
        return self.name

    def get_prerequisites(self):
        return self.__class__._default_manager.filter(
            is_required=True,
            sequence_number__lt=self.sequence_number).order_by('sequence_number')


class AbstractOrderDiscount(models.Model):
    """
    A discount against an order.

    Normally only used for display purposes so an order can be listed with discounts displayed
    separately even though in reality, the discounts are applied at the line level.
    """
    order = models.ForeignKey('order.Order', related_name="discounts")
    offer_id = models.PositiveIntegerField(_('Offer ID'), blank=True, null=True)
    voucher_id = models.PositiveIntegerField(_('Voucher ID'), blank=True, null=True)
    voucher_code = models.CharField(_("Code"), max_length=128, db_index=True, null=True)
    amount = models.DecimalField(_('Amount'), decimal_places=2, max_digits=12, default=0)

    class Meta:
        abstract = True
        verbose_name = _("Order Discount")
        verbose_name_plural = _("Order Discounts")

    def __unicode__(self):
        return _("Discount of %(amount)r from order %(order)s") % {'amount': self.amount, 'order': self.order}

    @property
    def offer(self):
        Offer = models.get_model('offer', 'ConditionalOffer')
        try:
            return Offer.objects.get(id=self.offer_id)
        except Offer.DoesNotExist:
            return None

    @property
    def voucher(self):
        Voucher = models.get_model('voucher', 'Voucher')
        try:
            return Voucher.objects.get(id=self.offer_id)
        except Voucher.DoesNotExist:
            return None

    def description(self):
        if self.voucher_code:
            return self.voucher_code
        return self.offer.name
