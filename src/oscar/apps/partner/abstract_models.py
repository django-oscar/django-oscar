from django.db import models, router
from django.db.models import F, signals
from django.db.models.functions import Coalesce, Least
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.apps.partner.exceptions import InvalidStockAdjustment
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.models.fields import AutoSlugField


class AbstractPartner(models.Model):
    """
    A fulfilment partner. An individual or company who can fulfil products.
    E.g. for physical goods, somebody with a warehouse and means of delivery.

    Creating one or more instances of the Partner model is a required step in
    setting up an Oscar deployment. Many Oscar deployments will only have one
    fulfilment partner.
    """
    code = AutoSlugField(_("Code"), max_length=128, unique=True, db_index=True,
                         populate_from='name')
    name = models.CharField(
        pgettext_lazy("Partner's name", "Name"), max_length=128, blank=True, db_index=True)

    #: A partner can have users assigned to it. This is used
    #: for access modelling in the permission-based dashboard
    users = models.ManyToManyField(
        AUTH_USER_MODEL, related_name="partners",
        blank=True, verbose_name=_("Users"))

    @property
    def display_name(self):
        return self.name or self.code

    @property
    def primary_address(self):
        """
        Returns a partners primary address. Usually that will be the
        headquarters or similar.

        This is a rudimentary implementation that raises an error if there's
        more than one address. If you actually want to support multiple
        addresses, you will likely need to extend PartnerAddress to have some
        field or flag to base your decision on.
        """
        addresses = self.addresses.all()
        if len(addresses) == 0:  # intentionally using len() to save queries
            return None
        elif len(addresses) == 1:
            return addresses[0]
        else:
            raise NotImplementedError(
                "Oscar's default implementation of primary_address only "
                "supports one PartnerAddress.  You need to override the "
                "primary_address to look up the right address")

    def get_address_for_stockrecord(self, stockrecord):
        """
        Stock might be coming from different warehouses. Overriding this
        function allows selecting the correct PartnerAddress for the record.
        That can be useful when determining tax.
        """
        return self.primary_address

    class Meta:
        abstract = True
        app_label = 'partner'
        ordering = ('name', 'code')
        permissions = (('dashboard_access', 'Can access dashboard'), )
        verbose_name = _('Fulfillment partner')
        verbose_name_plural = _('Fulfillment partners')

    def __str__(self):
        return self.display_name


class AbstractStockRecord(models.Model):
    """
    A stock record.

    This records information about a product from a fulfilment partner, such as
    their SKU, the number they have in stock and price information.

    Stockrecords are used by 'strategies' to determine availability and pricing
    information for the customer.
    """
    product = models.ForeignKey(
        'catalogue.Product',
        on_delete=models.CASCADE,
        related_name="stockrecords",
        verbose_name=_("Product"))
    partner = models.ForeignKey(
        'partner.Partner',
        on_delete=models.CASCADE,
        verbose_name=_("Partner"),
        related_name='stockrecords')

    #: The fulfilment partner will often have their own SKU for a product,
    #: which we store here.  This will sometimes be the same the product's UPC
    #: but not always.  It should be unique per partner.
    #: See also http://en.wikipedia.org/wiki/Stock-keeping_unit
    partner_sku = models.CharField(_("Partner SKU"), max_length=128)

    # Price info:
    price_currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency)

    # This is the base price for calculations - whether this is inclusive or exclusive of
    # tax depends on your implementation, as this is highly domain-specific.
    # It is nullable because some items don't have a fixed
    # price but require a runtime calculation (possibly from an external service).
    price = models.DecimalField(
        _("Price"), decimal_places=2, max_digits=12,
        blank=True, null=True)

    #: Number of items in stock
    num_in_stock = models.PositiveIntegerField(
        _("Number in stock"), blank=True, null=True)

    #: The amount of stock allocated to orders but not fed back to the master
    #: stock system.  A typical stock update process will set the
    #: :py:attr:`.num_in_stock` variable to a new value and reset
    #: :py:attr:`.num_allocated` to zero.
    num_allocated = models.IntegerField(
        _("Number allocated"), blank=True, null=True)

    #: Threshold for low-stock alerts.  When stock goes beneath this threshold,
    #: an alert is triggered so warehouse managers can order more.
    low_stock_threshold = models.PositiveIntegerField(
        _("Low Stock Threshold"), blank=True, null=True)

    # Date information
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date updated"), auto_now=True,
                                        db_index=True)

    def __str__(self):
        msg = "Partner: %s, product: %s" % (
            self.partner.display_name, self.product,)
        if self.partner_sku:
            msg = "%s (%s)" % (msg, self.partner_sku)
        return msg

    class Meta:
        abstract = True
        app_label = 'partner'
        unique_together = ('partner', 'partner_sku')
        verbose_name = _("Stock record")
        verbose_name_plural = _("Stock records")

    @property
    def net_stock_level(self):
        """
        The effective number in stock (e.g. available to buy).

        This is correct property to show the customer, not the
        :py:attr:`.num_in_stock` field as that doesn't account for allocations.
        This can be negative in some unusual circumstances
        """
        if self.num_in_stock is None:
            return 0
        if self.num_allocated is None:
            return self.num_in_stock
        return self.num_in_stock - self.num_allocated

    @cached_property
    def can_track_allocations(self):
        """Return True if the Product is set for stock tracking."""
        return self.product.get_product_class().track_stock

    # 2-stage stock management model

    def allocate(self, quantity):
        """
        Record a stock allocation.

        This normally happens when a product is bought at checkout.  When the
        product is actually shipped, then we 'consume' the allocation.

        """
        # Doesn't make sense to allocate if stock tracking is off.
        if not self.can_track_allocations:
            return

        # Send the pre-save signal
        self.pre_save_signal()

        # Atomic update
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=(Coalesce(F("num_allocated"), 0) + quantity)
            )
        )

        # Make sure the current object is up-to-date
        self.refresh_from_db(fields=["num_allocated"])

        # Send the post-save signal
        self.post_save_signal()

    allocate.alters_data = True

    def is_allocation_consumption_possible(self, quantity):
        """
        Test if a proposed stock consumption is permitted
        """
        return quantity <= min(self.num_allocated, self.num_in_stock)

    def consume_allocation(self, quantity):
        """
        Consume a previous allocation

        This is used when an item is shipped.  We remove the original
        allocation and adjust the number in stock accordingly
        """
        if not self.can_track_allocations:
            return
        if not self.is_allocation_consumption_possible(quantity):
            raise InvalidStockAdjustment(
                _('Invalid stock consumption request'))

        # send the pre save signal
        self.pre_save_signal()

        # Atomically consume allocations and stock
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=(Coalesce(F("num_allocated"), 0) - quantity),
                num_in_stock=(Coalesce(F("num_in_stock"), 0) - quantity),
            )
        )

        # Make sure current object is up-to-date
        self.refresh_from_db(fields=["num_allocated", "num_in_stock"])

        # Send the post-save signal
        self.post_save_signal()

    consume_allocation.alters_data = True

    def cancel_allocation(self, quantity):
        if not self.can_track_allocations:
            return

        # send the pre save signal
        self.pre_save_signal()

        # Atomically consume allocations
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=Coalesce(F("num_allocated"), 0)
                - Least(Coalesce(F("num_allocated"), 0), quantity),
            )
        )

        # Make sure current object is up-to-date
        self.refresh_from_db(fields=["num_allocated"])

        # Send the post-save signal
        self.post_save_signal()

    cancel_allocation.alters_data = True

    def pre_save_signal(self):
        signals.pre_save.send(
            sender=self.__class__,
            instance=self,
            created=False,
            raw=False,
            using=router.db_for_write(self.__class__, instance=self))

    def post_save_signal(self):
        signals.post_save.send(
            sender=self.__class__,
            instance=self,
            created=False,
            raw=False,
            using=router.db_for_write(self.__class__, instance=self))

    @property
    def is_below_threshold(self):
        if self.low_stock_threshold is None:
            return False
        return self.net_stock_level < self.low_stock_threshold


class AbstractStockAlert(models.Model):
    """
    A stock alert. E.g. used to notify users when a product is 'back in stock'.
    """
    stockrecord = models.ForeignKey(
        'partner.StockRecord',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_("Stock Record"))
    threshold = models.PositiveIntegerField(_("Threshold"))
    OPEN, CLOSED = "Open", "Closed"
    status_choices = (
        (OPEN, _("Open")),
        (CLOSED, _("Closed")),
    )
    status = models.CharField(_("Status"), max_length=128, default=OPEN,
                              choices=status_choices)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True, db_index=True)
    date_closed = models.DateTimeField(_("Date Closed"), blank=True, null=True)

    def close(self):
        self.status = self.CLOSED
        self.date_closed = now()
        self.save()
    close.alters_data = True

    def __str__(self):
        return _('<stockalert for "%(stock)s" status %(status)s>') \
            % {'stock': self.stockrecord, 'status': self.status}

    class Meta:
        abstract = True
        app_label = 'partner'
        ordering = ('-date_created',)
        verbose_name = _('Stock alert')
        verbose_name_plural = _('Stock alerts')
