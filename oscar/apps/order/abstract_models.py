from itertools import chain
from decimal import Decimal as D
import hashlib

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import slugify
from . import exceptions


class AbstractOrder(models.Model):
    """
    The main order model
    """
    number = models.CharField(_("Order number"), max_length=128, db_index=True)

    # We track the site that each order is placed within
    site = models.ForeignKey('sites.Site', verbose_name=_("Site"))
    basket_id = models.PositiveIntegerField(
        _("Basket ID"), null=True, blank=True)

    # Orders can be anonymous so we don't always have a customer ID
    user = models.ForeignKey(
        AUTH_USER_MODEL, related_name='orders', null=True, blank=True,
        verbose_name=_("User"))

    # Billing address is not always required (eg paying by gift card)
    billing_address = models.ForeignKey(
        'order.BillingAddress', null=True, blank=True,
        verbose_name=_("Billing Address"))

    # Total price looks like it could be calculated by adding up the
    # prices of the associated lines, but in some circumstances extra
    # order-level charges are added and so we need to store it separately
    currency = models.CharField(
        _("Currency"), max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY)
    total_incl_tax = models.DecimalField(
        _("Order total (inc. tax)"), decimal_places=2, max_digits=12)
    total_excl_tax = models.DecimalField(
        _("Order total (excl. tax)"), decimal_places=2, max_digits=12)

    # Shipping charges
    shipping_incl_tax = models.DecimalField(
        _("Shipping charge (inc. tax)"), decimal_places=2, max_digits=12,
        default=0)
    shipping_excl_tax = models.DecimalField(
        _("Shipping charge (excl. tax)"), decimal_places=2, max_digits=12,
        default=0)

    # Not all lines are actually shipped (such as downloads), hence shipping
    # address is not mandatory.
    shipping_address = models.ForeignKey(
        'order.ShippingAddress', null=True, blank=True,
        verbose_name=_("Shipping Address"))
    shipping_method = models.CharField(
        _("Shipping method"), max_length=128, null=True, blank=True)

    # Identifies shipping code
    shipping_code = models.CharField(blank=True, max_length=128, default="")

    # Use this field to indicate that an order is on hold / awaiting payment
    status = models.CharField(
        _("Status"), max_length=100, null=True, blank=True)

    guest_email = models.EmailField(
        _("Guest email address"), null=True, blank=True)

    # Index added to this field for reporting
    date_placed = models.DateTimeField(auto_now_add=True, db_index=True)

    #: Order status pipeline.  This should be a dict where each (key, value) #:
    #: corresponds to a status and a list of possible statuses that can follow
    #: that one.
    pipeline = getattr(settings, 'OSCAR_ORDER_STATUS_PIPELINE', {})

    #: Order status cascade pipeline.  This should be a dict where each (key,
    #: value) pair corresponds to an *order* status and the corresponding
    #: *line* status that needs to be set when the order is set to the new
    #: status
    cascade = getattr(settings, 'OSCAR_ORDER_STATUS_CASCADE', {})

    @classmethod
    def all_statuses(cls):
        """
        Return all possible statuses for an order
        """
        return cls.pipeline.keys()

    def available_statuses(self):
        """
        Return all possible statuses that this order can move to
        """
        return self.pipeline.get(self.status, ())

    def set_status(self, new_status):
        """
        Set a new status for this order.

        If the requested status is not valid, then ``InvalidOrderStatus`` is
        raised.
        """
        if new_status == self.status:
            return
        if new_status not in self.available_statuses():
            raise exceptions.InvalidOrderStatus(
                _("'%(new_status)s' is not a valid status for order %(number)s"
                  " (current status: '%(status)s')")
                % {'new_status': new_status,
                   'number': self.number,
                   'status': self.status})
        self.status = new_status
        if new_status in self.cascade:
            for line in self.lines.all():
                line.status = self.cascade[self.status]
                line.save()
        self.save()
    set_status.alters_data = True

    @property
    def is_anonymous(self):
        return self.user is None

    @property
    def basket_total_before_discounts_incl_tax(self):
        """
        Return basket total including tax but before discounts are applied
        """
        total = D('0.00')
        for line in self.lines.all():
            total += line.line_price_before_discounts_incl_tax
        return total

    @property
    def basket_total_before_discounts_excl_tax(self):
        """
        Return basket total excluding tax but before discounts are applied
        """
        total = D('0.00')
        for line in self.lines.all():
            total += line.line_price_before_discounts_excl_tax
        return total

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
        return (self.basket_total_before_discounts_incl_tax +
                self.shipping_incl_tax)

    @property
    def total_before_discounts_excl_tax(self):
        return (self.basket_total_before_discounts_excl_tax +
                self.shipping_excl_tax)

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
    def shipping_tax(self):
        return self.shipping_incl_tax - self.shipping_excl_tax

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
            map[event_name] = list(chain(map[event_name],
                                         event.line_quantities.all()))

        # Determine last complete event
        status = _("In progress")
        for event_name, event_line_quantities in map.items():
            if self._is_event_complete(event_line_quantities):
                status = event_name
        return status

    @property
    def has_shipping_discounts(self):
        return len(self.shipping_discounts) > 0

    @property
    def shipping_before_discounts_incl_tax(self):
        # We can construct what shipping would have been before discounts by
        # adding the discounts back onto the final shipping charge.
        total = D('0.00')
        for discount in self.shipping_discounts:
            total += discount.amount
        return self.shipping_incl_tax + total

    def _is_event_complete(self, event_quantities):
        # Form map of line to quantity
        map = {}
        for event_quantity in event_quantities:
            line_id = event_quantity.line_id
            map.setdefault(line_id, 0)
            map[line_id] += event_quantity.quantity

        for line in self.lines.all():
            if map[line.id] != line.quantity:
                return False
        return True

    class Meta:
        abstract = True
        ordering = ['-date_placed']
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __unicode__(self):
        return u"#%s" % (self.number,)

    def verification_hash(self):
        hash = hashlib.md5('%s%s' % (self.number, settings.SECRET_KEY))
        return hash.hexdigest()

    @property
    def email(self):
        if not self.user:
            return self.guest_email
        return self.user.email

    @property
    def basket_discounts(self):
        # This includes both offer- and voucher- discounts.  For orders we
        # don't need to treat them differently like we do for baskets.
        return self.discounts.filter(
            category=AbstractOrderDiscount.BASKET)

    @property
    def shipping_discounts(self):
        return self.discounts.filter(
            category=AbstractOrderDiscount.SHIPPING)

    @property
    def post_order_actions(self):
        return self.discounts.filter(
            category=AbstractOrderDiscount.DEFERRED)


class AbstractOrderNote(models.Model):
    """
    A note against an order.

    This are often used for audit purposes too.  IE, whenever an admin
    makes a change to an order, we create a note to record what happened.
    """
    order = models.ForeignKey('order.Order', related_name="notes",
                              verbose_name=_("Order"))

    # These are sometimes programatically generated so don't need a
    # user everytime
    user = models.ForeignKey(AUTH_USER_MODEL, null=True,
                             verbose_name=_("User"))

    # We allow notes to be classified although this isn't always needed
    INFO, WARNING, ERROR, SYSTEM = 'Info', 'Warning', 'Error', 'System'
    note_type = models.CharField(_("Note Type"), max_length=128, null=True)

    message = models.TextField(_("Message"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True)

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
        delta = timezone.now() - self.date_updated
        return delta.seconds < self.editable_lifetime


class AbstractCommunicationEvent(models.Model):
    """
    An order-level event involving a communication to the customer, such
    as an confirmation email being sent.
    """
    order = models.ForeignKey(
        'order.Order', related_name="communication_events",
        verbose_name=_("Order"))
    event_type = models.ForeignKey(
        'customer.CommunicationEventType', verbose_name=_("Event Type"))
    date_created = models.DateTimeField(_("Date"), auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Communication Event")
        verbose_name_plural = _("Communication Events")
        ordering = ['-date_created']

    def __unicode__(self):
        return _("'%(type)s' event for order #%(number)s") \
            % {'type': self.event_type.name, 'number': self.order.number}


# LINES


class AbstractLine(models.Model):
    """
    A order line (basically a product and a quantity)

    Not using a line model as it's difficult to capture and payment
    information when it splits across a line.
    """
    order = models.ForeignKey(
        'order.Order', related_name='lines', verbose_name=_("Order"))

    # We store the partner, their SKU and the title for cases where the product
    # has been deleted from the catalogue.  We also store the partner name in
    # case the partner gets deleted at a later date.
    partner = models.ForeignKey(
        'partner.Partner', related_name='order_lines', blank=True, null=True,
        on_delete=models.SET_NULL, verbose_name=_("Partner"))
    # We keep a link to the stockrecord used for this line which allows us to
    # update stocklevels when it ships
    stockrecord = models.ForeignKey(
        'partner.StockRecord', on_delete=models.SET_NULL, blank=True,
        null=True, verbose_name=_("Stock record"))
    partner_name = models.CharField(_("Partner name"), max_length=128)
    partner_sku = models.CharField(_("Partner SKU"), max_length=128)

    title = models.CharField(_("Title"), max_length=255)
    upc = models.CharField(_("UPC"), max_length=128, blank=True, null=True)

    # We don't want any hard links between orders and the products table so we
    # allow this link to be NULLable.
    product = models.ForeignKey(
        'catalogue.Product', on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name=_("Product"))
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)

    # Price information (these fields are actually redundant as the information
    # can be calculated from the LinePrice models
    line_price_incl_tax = models.DecimalField(
        _("Price (inc. tax)"), decimal_places=2, max_digits=12)
    line_price_excl_tax = models.DecimalField(
        _("Price (excl. tax)"), decimal_places=2, max_digits=12)

    # Price information before discounts are applied
    line_price_before_discounts_incl_tax = models.DecimalField(
        _("Price before discounts (inc. tax)"),
        decimal_places=2, max_digits=12)
    line_price_before_discounts_excl_tax = models.DecimalField(
        _("Price before discounts (excl. tax)"),
        decimal_places=2, max_digits=12)

    # REPORTING FIELDS
    # Cost price (the price charged by the fulfilment partner for this
    # product).
    unit_cost_price = models.DecimalField(
        _("Unit Cost Price"), decimal_places=2, max_digits=12, blank=True,
        null=True)
    # Normal site price for item (without discounts)
    unit_price_incl_tax = models.DecimalField(
        _("Unit Price (inc. tax)"), decimal_places=2, max_digits=12,
        blank=True, null=True)
    unit_price_excl_tax = models.DecimalField(
        _("Unit Price (excl. tax)"), decimal_places=2, max_digits=12,
        blank=True, null=True)
    # Retail price at time of purchase
    unit_retail_price = models.DecimalField(
        _("Unit Retail Price"), decimal_places=2, max_digits=12,
        blank=True, null=True)

    # Partner information
    partner_line_reference = models.CharField(
        _("Partner reference"), max_length=128, blank=True, null=True,
        help_text=_("This is the item number that the partner uses "
                    "within their system"))
    partner_line_notes = models.TextField(
        _("Partner Notes"), blank=True, null=True)

    # Partners often want to assign some status to each line to help with their
    # own business processes.
    status = models.CharField(_("Status"), max_length=255,
                              null=True, blank=True)

    # Estimated dispatch date - should be set at order time
    est_dispatch_date = models.DateField(
        _("Estimated Dispatch Date"), blank=True, null=True)

    #: Order status pipeline.  This should be a dict where each (key, value)
    #: corresponds to a status and the possible statuses that can follow that
    #: one.
    pipeline = getattr(settings, 'OSCAR_LINE_STATUS_PIPELINE', {})

    class Meta:
        abstract = True
        verbose_name = _("Order Line")
        verbose_name_plural = _("Order Lines")

    def __unicode__(self):
        if self.product:
            title = self.product.title
        else:
            title = _('<missing product>')
        return _("Product '%(name)s', quantity '%(qty)s'") % {
            'name': title, 'qty': self.quantity}

    @classmethod
    def all_statuses(cls):
        """
        Return all possible statuses for an order line
        """
        return cls.pipeline.keys()

    def available_statuses(self):
        """
        Return all possible statuses that this order line can move to
        """
        return self.pipeline.get(self.status, ())

    def set_status(self, new_status):
        """
        Set a new status for this line

        If the requested status is not valid, then ``InvalidLineStatus`` is
        raised.
        """
        if new_status == self.status:
            return
        if new_status not in self.available_statuses():
            raise exceptions.InvalidLineStatus(
                _("'%(new_status)s' is not a valid status (current status:"
                  " '%(status)s')")
                % {'new_status': new_status, 'status': self.status})
        self.status = new_status
        self.save()
    set_status.alters_data = True

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
        return self.line_price_before_discounts_incl_tax \
            - self.line_price_incl_tax

    @property
    def discount_excl_tax(self):
        return self.line_price_before_discounts_excl_tax \
            - self.line_price_excl_tax

    @property
    def line_price_tax(self):
        return self.line_price_incl_tax - self.line_price_excl_tax

    @property
    def unit_price_tax(self):
        return self.unit_price_incl_tax - self.unit_price_excl_tax

    # Shipping status helpers

    @property
    def shipping_status(self):
        """
        Returns a string summary of the shipping status of this line
        """
        status_map = self.shipping_event_breakdown
        if not status_map:
            return ''

        events = []
        last_complete_event_name = None
        for event_dict in status_map.values():
            if event_dict['quantity'] == self.quantity:
                events.append(event_dict['name'])
                last_complete_event_name = event_dict['name']
            else:
                events.append("%s (%d/%d items)" % (
                    event_dict['name'], event_dict['quantity'],
                    self.quantity))

        if last_complete_event_name == status_map.values()[-1]['name']:
            return last_complete_event_name

        return ', '.join(events)

    def is_shipping_event_permitted(self, event_type, quantity):
        """
        Test whether a shipping event with the given quantity is permitted

        This method should normally be overriden to ensure that the
        prerequisite shipping events have been passed for this line.
        """
        # Note, this calculation is simplistic - normally, you will also need
        # to check if previous shipping events have occurred.  Eg, you can't
        # return lines until they have been shipped.
        current_qty = self.shipping_event_quantity(event_type)
        return (current_qty + quantity) <= self.quantity

    def shipping_event_quantity(self, event_type):
        """
        Return the quantity of this line that has been involved in a shipping
        event of the passed type.
        """
        result = self.shipping_event_quantities.filter(
            event__event_type=event_type).aggregate(Sum('quantity'))
        if result['quantity__sum'] is None:
            return 0
        else:
            return result['quantity__sum']

    def has_shipping_event_occurred(self, event_type, quantity=None):
        """
        Test whether this line has passed a given shipping event
        """
        if not quantity:
            quantity = self.quantity
        return self.shipping_event_quantity(event_type) == quantity

    @property
    def shipping_event_breakdown(self):
        """
        Returns a dict of shipping events that this line has been through
        """
        status_map = {}
        for event in self.shipping_events.all():
            event_type = event.event_type
            event_name = event_type.name
            event_quantity = event.line_quantities.get(line=self).quantity
            if event_name in status_map:
                status_map[event_name]['quantity'] += event_quantity
            else:
                status_map[event_name] = {'event_type': event_type,
                                          'name': event_name,
                                          'quantity': event_quantity}
        return status_map

    # Payment event helpers

    def is_payment_event_permitted(self, event_type, quantity):
        """
        Test whether a payment event with the given quantity is permitted
        """
        current_qty = self.payment_event_quantity(event_type)
        return (current_qty + quantity) <= self.quantity

    def payment_event_quantity(self, event_type):
        """
        Return the quantity of this line that has been involved in a payment
        event of the passed type.
        """
        result = self.payment_event_quantities.filter(
            event__event_type=event_type).aggregate(Sum('quantity'))
        if result['quantity__sum'] is None:
            return 0
        else:
            return result['quantity__sum']

    @property
    def is_product_deleted(self):
        return self.product is None

    def is_available_to_reorder(self, basket, strategy):
        """
        Test if this line can be re-ordered using the passed strategy and
        basket
        """
        if not self.product:
            return False, (_("'%(title)s' is no longer available") %
                           {'title': self.title})

        try:
            basket_line = basket.lines.get(product=self.product)
        except basket.lines.model.DoesNotExist:
            desired_qty = self.quantity
        else:
            desired_qty = basket_line.quantity + self.quantity

        result = strategy.fetch_for_product(self.product)
        is_available, reason = result.availability.is_purchase_permitted(
            quantity=desired_qty)
        if not is_available:
            return False, reason
        return True, None


class AbstractLineAttribute(models.Model):
    """
    An attribute of a line
    """
    line = models.ForeignKey(
        'order.Line', related_name='attributes',
        verbose_name=_("Line"))
    option = models.ForeignKey(
        'catalogue.Option', null=True, on_delete=models.SET_NULL,
        related_name="line_attributes", verbose_name=_("Option"))
    type = models.CharField(_("Type"), max_length=128)
    value = models.CharField(_("Value"), max_length=255)

    class Meta:
        abstract = True
        verbose_name = _("Line Attribute")
        verbose_name_plural = _("Line Attributes")

    def __unicode__(self):
        return "%s = %s" % (self.type, self.value)


class AbstractLinePrice(models.Model):
    """
    For tracking the prices paid for each unit within a line.

    This is necessary as offers can lead to units within a line
    having different prices.  For example, one product may be sold at
    50% off as it's part of an offer while the remainder are full price.
    """
    order = models.ForeignKey(
        'order.Order', related_name='line_prices', verbose_name=_("Option"))
    line = models.ForeignKey(
        'order.Line', related_name='prices', verbose_name=_("Line"))
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    price_incl_tax = models.DecimalField(
        _("Price (inc. tax)"), decimal_places=2, max_digits=12)
    price_excl_tax = models.DecimalField(
        _("Price (excl. tax)"), decimal_places=2, max_digits=12)
    shipping_incl_tax = models.DecimalField(
        _("Shiping (inc. tax)"), decimal_places=2, max_digits=12, default=0)
    shipping_excl_tax = models.DecimalField(
        _("Shipping (excl. tax)"), decimal_places=2, max_digits=12, default=0)

    class Meta:
        abstract = True
        ordering = ('id',)
        verbose_name = _("Line Price")
        verbose_name_plural = _("Line Prices")

    def __unicode__(self):
        return _("Line '%(number)s' (quantity %(qty)d) price %(price)s") % {
            'number': self.line,
            'qty': self.quantity,
            'price': self.price_incl_tax}


# PAYMENT EVENTS


class AbstractPaymentEventType(models.Model):
    """
    Payment event types are things like 'Paid', 'Failed', 'Refunded'.

    These are effectively the transaction types.
    """
    name = models.CharField(_("Name"), max_length=128, unique=True)
    code = models.SlugField(_("Code"), max_length=128, unique=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractPaymentEventType, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        verbose_name = _("Payment Event Type")
        verbose_name_plural = _("Payment Event Types")
        ordering = ('name', )

    def __unicode__(self):
        return self.name


class AbstractPaymentEvent(models.Model):
    """
    A payment event for an order

    For example:

    * All lines have been paid for
    * 2 lines have been refunded
    """
    order = models.ForeignKey(
        'order.Order', related_name='payment_events',
        verbose_name=_("Order"))
    amount = models.DecimalField(
        _("Amount"), decimal_places=2, max_digits=12)
    # The reference should refer to the transaction ID of the payment gateway
    # that was used for this event.
    reference = models.CharField(
        _("Reference"), max_length=128, blank=True)
    lines = models.ManyToManyField(
        'order.Line', through='PaymentEventQuantity',
        verbose_name=_("Lines"))
    event_type = models.ForeignKey(
        'order.PaymentEventType', verbose_name=_("Event Type"))
    # Allow payment events to be linked to shipping events.  Often a shipping
    # event will trigger a payment event and so we can use this FK to capture
    # the relationship.
    shipping_event = models.ForeignKey(
        'order.ShippingEvent', related_name='payment_events',
        null=True)
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Payment Event")
        verbose_name_plural = _("Payment Events")
        ordering = ['-date_created']

    def __unicode__(self):
        return _("Payment event for order %s") % self.order

    def num_affected_lines(self):
        return self.lines.all().count()


class PaymentEventQuantity(models.Model):
    """
    A "through" model linking lines to payment events
    """
    event = models.ForeignKey(
        'order.PaymentEvent', related_name='line_quantities',
        verbose_name=_("Event"))
    line = models.ForeignKey(
        'order.Line', related_name="payment_event_quantities",
        verbose_name=_("Line"))
    quantity = models.PositiveIntegerField(_("Quantity"))

    class Meta:
        verbose_name = _("Payment Event Quantity")
        verbose_name_plural = _("Payment Event Quantities")


# SHIPPING EVENTS


class AbstractShippingEvent(models.Model):
    """
    An event is something which happens to a group of lines such as
    1 item being dispatched.
    """
    order = models.ForeignKey(
        'order.Order', related_name='shipping_events', verbose_name=_("Order"))
    lines = models.ManyToManyField(
        'order.Line', related_name='shipping_events',
        through='ShippingEventQuantity', verbose_name=_("Lines"))
    event_type = models.ForeignKey(
        'order.ShippingEventType', verbose_name=_("Event Type"))
    notes = models.TextField(
        _("Event notes"), blank=True, null=True,
        help_text=_("This could be the dispatch reference, or a "
                    "tracking number"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Shipping Event")
        verbose_name_plural = _("Shipping Events")
        ordering = ['-date_created']

    def __unicode__(self):
        return _("Order #%(number)s, type %(type)s") % {
            'number': self.order.number,
            'type': self.event_type}

    def num_affected_lines(self):
        return self.lines.count()


class ShippingEventQuantity(models.Model):
    """
    A "through" model linking lines to shipping events.

    This exists to track the quantity of a line that is involved in a
    particular shipping event.
    """
    event = models.ForeignKey(
        'order.ShippingEvent', related_name='line_quantities',
        verbose_name=_("Event"))
    line = models.ForeignKey(
        'order.Line', related_name="shipping_event_quantities",
        verbose_name=_("Line"))
    quantity = models.PositiveIntegerField(_("Quantity"))

    class Meta:
        verbose_name = _("Shipping Event Quantity")
        verbose_name_plural = _("Shipping Event Quantities")

    def save(self, *args, **kwargs):
        # Default quantity to full quantity of line
        if not self.quantity:
            self.quantity = self.line.quantity
        # Ensure we don't violate quantities constraint
        if not self.line.is_shipping_event_permitted(
                self.event.event_type, self.quantity):
            raise exceptions.InvalidShippingEvent
        super(ShippingEventQuantity, self).save(*args, **kwargs)

    def __unicode__(self):
        return _("%(product)s - quantity %(qty)d") % {
            'product': self.line.product,
            'qty': self.quantity}


class AbstractShippingEventType(models.Model):
    """
    A type of shipping/fulfillment event

    Eg: 'Shipped', 'Cancelled', 'Returned'
    """
    # Name is the friendly description of an event
    name = models.CharField(_("Name"), max_length=255, unique=True)
    # Code is used in forms
    code = models.SlugField(_("Code"), max_length=128, unique=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractShippingEventType, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        verbose_name = _("Shipping Event Type")
        verbose_name_plural = _("Shipping Event Types")
        ordering = ('name', )

    def __unicode__(self):
        return self.name


# DISCOUNTS


class AbstractOrderDiscount(models.Model):
    """
    A discount against an order.

    Normally only used for display purposes so an order can be listed with
    discounts displayed separately even though in reality, the discounts are
    applied at the line level.

    This has evolved to be a slightly misleading class name as this really
    track benefit applications which aren't necessarily discounts.
    """
    order = models.ForeignKey(
        'order.Order', related_name="discounts", verbose_name=_("Order"))

    # We need to distinguish between basket discounts, shipping discounts and
    # 'deferred' discounts.
    BASKET, SHIPPING, DEFERRED = "Basket", "Shipping", "Deferred"
    CATEGORY_CHOICES = (
        (BASKET, _(BASKET)),
        (SHIPPING, _(SHIPPING)),
        (DEFERRED, _(DEFERRED)),
    )
    category = models.CharField(
        _("Discount category"), default=BASKET, max_length=64,
        choices=CATEGORY_CHOICES)

    offer_id = models.PositiveIntegerField(
        _("Offer ID"), blank=True, null=True)
    offer_name = models.CharField(
        _("Offer name"), max_length=128, db_index=True, null=True)
    voucher_id = models.PositiveIntegerField(
        _("Voucher ID"), blank=True, null=True)
    voucher_code = models.CharField(
        _("Code"), max_length=128, db_index=True, null=True)
    frequency = models.PositiveIntegerField(_("Frequency"), null=True)
    amount = models.DecimalField(
        _("Amount"), decimal_places=2, max_digits=12, default=0)

    # Post-order offer applications can return a message to indicate what
    # action was taken after the order was placed.
    message = models.TextField(blank=True, null=True)

    @property
    def is_basket_discount(self):
        return self.category == self.BASKET

    @property
    def is_shipping_discount(self):
        return self.category == self.SHIPPING

    @property
    def is_post_order_action(self):
        return self.category == self.DEFERRED

    class Meta:
        abstract = True
        verbose_name = _("Order Discount")
        verbose_name_plural = _("Order Discounts")

    def save(self, **kwargs):
        if self.offer_id and not self.offer_name:
            offer = self.offer
            if offer:
                self.offer_name = offer.name

        if self.voucher_id and not self.voucher_code:
            voucher = self.voucher
            if voucher:
                self.voucher_code = voucher.code

        super(AbstractOrderDiscount, self).save(**kwargs)

    def __unicode__(self):
        return _("Discount of %(amount)r from order %(order)s") % {
            'amount': self.amount, 'order': self.order}

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
            return Voucher.objects.get(id=self.voucher_id)
        except Voucher.DoesNotExist:
            return None

    def description(self):
        if self.voucher_code:
            return self.voucher_code
        return self.offer_name or u""
