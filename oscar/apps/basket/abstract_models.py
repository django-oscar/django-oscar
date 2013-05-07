from decimal import Decimal
import zlib

from django.db import models
from django.db.models import query
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from oscar.apps.basket.managers import OpenBasketManager, SavedBasketManager
from oscar.apps.offer import results
from oscar.templatetags.currency_filters import currency


class AbstractBasket(models.Model):
    """
    Basket object
    """
    # Baskets can be anonymously owned - hence this field is nullable.  When a
    # anon user signs in, their two baskets are merged.
    owner = models.ForeignKey(
        'auth.User', related_name='baskets', null=True,
        verbose_name=_("Owner"))

    # Basket statuses
    # - Frozen is for when a basket is in the process of being submitted
    #   and we need to prevent any changes to it.
    OPEN, MERGED, SAVED, FROZEN, SUBMITTED = (
        "Open", "Merged", "Saved", "Frozen", "Submitted")
    STATUS_CHOICES = (
        (OPEN, _("Open - currently active")),
        (MERGED, _("Merged - superceded by another basket")),
        (SAVED, _("Saved - for items to be purchased later")),
        (FROZEN, _("Frozen - the basket cannot be modified")),
        (SUBMITTED, _("Submitted - has been ordered at the checkout")),
    )
    status = models.CharField(
        _("Status"), max_length=128, default=OPEN, choices=STATUS_CHOICES)

    # A basket can have many vouchers attached to it.  However, it is common
    # for sites to only allow one voucher per basket - this will need to be
    # enforced in the project's codebase.
    vouchers = models.ManyToManyField(
        'voucher.Voucher', null=True, verbose_name=_("Vouchers"), blank=True)

    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_merged = models.DateTimeField(_("Date merged"), null=True, blank=True)
    date_submitted = models.DateTimeField(_("Date submitted"), null=True,
                                          blank=True)

    # Only if a basket is in one of these statuses can it be edited
    editable_statuses = (OPEN, SAVED)

    class Meta:
        abstract = True
        verbose_name = _('Basket')
        verbose_name_plural = _('Baskets')

    objects = models.Manager()
    open = OpenBasketManager()
    saved = SavedBasketManager()

    def __init__(self, *args, **kwargs):
        super(AbstractBasket, self).__init__(*args, **kwargs)
        # We keep a cached copy of the basket lines as we refer to them often
        # within the same request cycle.  Also, applying offers will append
        # discount data to the basket lines which isn't persisted to the DB and
        # so we want to avoid reloading them as this would drop the discount
        # information.
        self._lines = None  # Cached queryset of lines
        self.offer_applications = results.OfferApplications()
        self.exempt_from_tax = False

    def __unicode__(self):
        return _(
            u"%(status)s basket (owner: %(owner)s, lines: %(num_lines)d)") % {
                'status': self.status,
                'owner': self.owner,
                'num_lines': self.num_lines}

    def all_lines(self):
        """
        Return a cached set of basket lines.

        This is important for offers as they alter the line models and you
        don't want to reload them from the DB as that information would be
        lost.
        """
        if self.id is None:
            return query.EmptyQuerySet(model=self.__class__)
        if self._lines is None:
            self._lines = self.lines.select_related(
                'product', 'product__stockrecord'
            ).all().prefetch_related('attributes', 'product__images')
        return self._lines

    def is_quantity_allowed(self, qty):
        basket_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.num_items
            max_allowed = basket_threshold - total_basket_quantity
            if qty > max_allowed:
                return False, _(
                    "Due to technical limitations we are not able "
                    "to ship more than %(threshold)d items in one order.") % {
                        'threshold': basket_threshold,
                    }
        return True, None

    # ============
    # Manipulation
    # ============

    def flush(self):
        """Remove all lines from basket."""
        if self.status == self.FROZEN:
            raise PermissionDenied("A frozen basket cannot be flushed")
        self.lines.all().delete()
        self._lines = None

    def add_product(self, product, quantity=1, options=None):
        """
        Add a product to the basket

        The 'options' list should contains dicts with keys 'option' and 'value'
        which link the relevant product.Option model and string value
        respectively.
        """
        if options is None:
            options = []
        if not self.id:
            self.save()

        # Line reference is used to distinguish between variations of the same
        # product (eg T-shirts with different personalisations)
        line_ref = self._create_line_reference(product, options)

        # Determine price to store (if one exists).  It is only stored for
        # audit and sometimes caching.
        price_excl_tax, price_incl_tax = None, None
        if product.has_stockrecord:
            stockrecord = product.stockrecord
            if stockrecord:
                price_excl_tax = getattr(stockrecord, 'price_excl_tax', None)
                price_incl_tax = getattr(stockrecord, 'price_incl_tax', None)

        line, created = self.lines.get_or_create(
            line_reference=line_ref,
            product=product,
            defaults={'quantity': quantity,
                      'price_excl_tax': price_excl_tax,
                      'price_incl_tax': price_incl_tax})
        if created:
            for option_dict in options:
                line.attributes.create(option=option_dict['option'],
                                       value=option_dict['value'])
        else:
            line.quantity += quantity
            line.save()
        self.reset_offer_applications()
    add_product.alters_data = True

    def applied_offers(self):
        """
        Return a dict of offers successfully applied to the basket.

        This is used to compare offers before and after a basket change to see
        if there is a difference.
        """
        return self.offer_applications.offers

    def reset_offer_applications(self):
        """
        Remove any discounts so they get recalculated
        """
        self.offer_applications = results.OfferApplications()
        self._lines = None

    def merge_line(self, line, add_quantities=True):
        """
        For transferring a line from another basket to this one.

        This is used with the "Saved" basket functionality.
        """
        try:
            existing_line = self.lines.get(line_reference=line.line_reference)
        except ObjectDoesNotExist:
            # Line does not already exist - reassign its basket
            line.basket = self
            line.save()
        else:
            # Line already exists - assume the max quantity is correct and
            # delete the old
            if add_quantities:
                existing_line.quantity += line.quantity
            else:
                existing_line.quantity = max(existing_line.quantity,
                                             line.quantity)
            existing_line.save()
            line.delete()
        finally:
            self._lines = None
    merge_line.alters_data = True

    def merge(self, basket, add_quantities=True):
        """
        Merges another basket with this one.

        :basket: The basket to merge into this one.
        :add_quantities: Whether to add line quantities when they are merged.
        """
        for line_to_merge in basket.all_lines():
            self.merge_line(line_to_merge, add_quantities)
        basket.status = self.MERGED
        basket.date_merged = now()
        basket._lines = None
        basket.save()
    merge.alters_data = True

    def freeze(self):
        """
        Freezes the basket so it cannot be modified.
        """
        self.status = self.FROZEN
        self.save()
    freeze.alters_data = True

    def thaw(self):
        """
        Unfreezes a basket so it can be modified again
        """
        self.status = self.OPEN
        self.save()
    thaw.alters_data = True

    def submit(self):
        """
        Mark this basket as submitted
        """
        self.status = self.SUBMITTED
        self.date_submitted = now()
        self.save()
    submit.alters_data = True

    # Kept for backwards compatibility
    set_as_submitted = submit

    def set_as_tax_exempt(self):
        self.exempt_from_tax = True
        for line in self.all_lines():
            line.set_as_tax_exempt()

    def is_shipping_required(self):
        """
        Test whether the basket contains physical products that require
        shipping.
        """
        for line in self.all_lines():
            if line.product.is_shipping_required:
                return True
        return False

    # =======
    # Helpers
    # =======

    def _create_line_reference(self, item, options):
        """
        Returns a reference string for a line based on the item
        and its options.
        """
        if not options:
            return item.id
        return "%d_%s" % (item.id, zlib.crc32(str(options)))

    def _get_total(self, property):
        """
        For executing a named method on each line of the basket
        and returning the total.
        """
        total = Decimal('0.00')
        for line in self.all_lines():
            try:
                total += getattr(line, property)
            except ObjectDoesNotExist:
                # Handle situation where the product may have been deleted
                pass
        return total

    # ==========
    # Properties
    # ==========

    @property
    def is_empty(self):
        """
        Test if this basket is empty
        """
        return self.id is None or self.num_lines == 0

    @property
    def total_excl_tax(self):
        """Return total line price excluding tax"""
        return self._get_total('line_price_excl_tax_and_discounts')

    @property
    def total_tax(self):
        """Return total tax for a line"""
        return self._get_total('line_tax')

    @property
    def total_incl_tax(self):
        """
        Return total price inclusive of tax and discounts
        """
        return self._get_total('line_price_incl_tax_and_discounts')

    @property
    def total_incl_tax_excl_discounts(self):
        """
        Return total price inclusive of tax but exclusive discounts
        """
        return self._get_total('line_price_incl_tax')

    @property
    def total_discount(self):
        return self._get_total('discount_value')

    @property
    def offer_discounts(self):
        """
        Return basket discounts from non-voucher sources.  Does not include
        shipping discounts.
        """
        return self.offer_applications.offer_discounts

    @property
    def voucher_discounts(self):
        """
        Return discounts from vouchers
        """
        return self.offer_applications.voucher_discounts

    @property
    def shipping_discounts(self):
        """
        Return discounts from vouchers
        """
        return self.offer_applications.shipping_discounts

    @property
    def post_order_actions(self):
        """
        Return discounts from vouchers
        """
        return self.offer_applications.post_order_actions

    @property
    def grouped_voucher_discounts(self):
        """
        Return discounts from vouchers but grouped so that a voucher which
        links to multiple offers is aggregated into one object.
        """
        return self.offer_applications.grouped_voucher_discounts

    @property
    def total_excl_tax_excl_discounts(self):
        """
        Return total price excluding tax and discounts
        """
        return self._get_total('line_price_excl_tax')

    @property
    def num_lines(self):
        """Return number of lines"""
        return len(self.all_lines())

    @property
    def num_items(self):
        """Return number of items"""
        return reduce(
            lambda num, line: num + line.quantity, self.all_lines(), 0)

    @property
    def num_items_without_discount(self):
        num = 0
        for line in self.all_lines():
            num += line.quantity_without_discount
        return num

    @property
    def num_items_with_discount(self):
        num = 0
        for line in self.all_lines():
            num += line.quantity_with_discount
        return num

    @property
    def time_before_submit(self):
        if not self.date_submitted:
            return None
        return self.date_submitted - self.date_created

    @property
    def time_since_creation(self, test_datetime=None):
        if not test_datetime:
            test_datetime = now()
        return test_datetime - self.date_created

    @property
    def contains_a_voucher(self):
        return self.vouchers.all().count() > 0

    # =============
    # Query methods
    # =============

    def can_be_edited(self):
        """
        Test if a basket can be edited
        """
        return self.status in self.editable_statuses

    def contains_voucher(self, code):
        """
        Test whether the basket contains a voucher with a given code
        """
        try:
            self.vouchers.get(code=code)
        except ObjectDoesNotExist:
            return False
        else:
            return True

    def line_quantity(self, product, options=None):
        """
        Return the current quantity of a specific product and options
        """
        ref = self._create_line_reference(product, options)
        try:
            return self.lines.get(line_reference=ref).quantity
        except ObjectDoesNotExist:
            return 0

    def is_submitted(self):
        return self.status == self.SUBMITTED


class AbstractLine(models.Model):
    """
    A line of a basket (product and a quantity)
    """
    basket = models.ForeignKey('basket.Basket', related_name='lines',
                               verbose_name=_("Basket"))

    # This is to determine which products belong to the same line
    # We can't just use product.id as you can have customised products
    # which should be treated as separate lines.  Set as a
    # SlugField as it is included in the path for certain views.
    line_reference = models.SlugField(_("Line Reference"), max_length=128,
                                      db_index=True)

    product = models.ForeignKey(
        'catalogue.Product', related_name='basket_lines',
        verbose_name=_("Product"))
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)

    # We store the unit price incl tax of the product when it is first added to
    # the basket.  This allows us to tell if a product has changed price since
    # a person first added it to their basket.
    price_excl_tax = models.DecimalField(
        _('Price excl. Tax'), decimal_places=2, max_digits=12,
        null=True)
    price_incl_tax = models.DecimalField(
        _('Price incl. Tax'), decimal_places=2, max_digits=12, null=True)
    # Track date of first addition
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    # Instance variables used to persist discount information
    _discount = Decimal('0.00')
    _affected_quantity = 0
    _charge_tax = True

    class Meta:
        abstract = True
        unique_together = ("basket", "line_reference")
        verbose_name = _('Basket line')
        verbose_name_plural = _('Basket lines')

    def __unicode__(self):
        return _(
            u"Basket #%(basket_id)d, Product #%(product_id)d, quantity %(quantity)d") % {
                'basket_id': self.basket.pk,
                'product_id': self.product.pk,
                'quantity': self.quantity}

    def save(self, *args, **kwargs):
        """
        Saves a line or deletes if the quantity is 0
        """
        if not self.basket.can_be_edited():
            raise PermissionDenied(
                _("You cannot modify a %s basket") % (
                    self.basket.status.lower(),))
        if self.quantity == 0:
            return self.delete(*args, **kwargs)
        return super(AbstractLine, self).save(*args, **kwargs)

    def set_as_tax_exempt(self):
        self._charge_tax = False

    # =============
    # Offer methods
    # =============

    def clear_discount(self):
        """
        Remove any discounts from this line.
        """
        self._discount = Decimal('0.00')
        self._affected_quantity = 0

    def discount(self, discount_value, affected_quantity):
        """
        Apply a discount
        """
        self._discount += discount_value
        self._affected_quantity += int(affected_quantity)

    def consume(self, quantity):
        """
        Mark all or part of the line as 'consumed'

        Consumed items are no longer available to be used in offers.
        """
        if quantity > self.quantity - self._affected_quantity:
            inc = self.quantity - self._affected_quantity
        else:
            inc = quantity
        self._affected_quantity += int(inc)

    def get_price_breakdown(self):
        """
        Return a breakdown of line prices after discounts have been applied.

        Returns a list of (unit_price_incl_tx, unit_price_excl_tax, quantity)
        tuples.
        """
        prices = []
        if not self.has_discount:
            prices.append((self.unit_price_incl_tax, self.unit_price_excl_tax,
                           self.quantity))
        else:
            # Need to split the discount among the affected quantity
            # of products.
            item_incl_tax_discount = (
                self._discount / int(self._affected_quantity))
            item_excl_tax_discount = item_incl_tax_discount * self._tax_ratio
            prices.append((self.unit_price_incl_tax - item_incl_tax_discount,
                           self.unit_price_excl_tax - item_excl_tax_discount,
                           self._affected_quantity))
            if self.quantity_without_discount:
                prices.append((self.unit_price_incl_tax,
                               self.unit_price_excl_tax,
                               self.quantity_without_discount))
        return prices

    # =======
    # Helpers
    # =======

    def _get_stockrecord_property(self, property):
        if not self.product.stockrecord:
            return Decimal('0.00')
        else:
            attr = getattr(self.product.stockrecord, property)
            if attr is None:
                attr = Decimal('0.00')
            return attr

    @property
    def _tax_ratio(self):
        if not self.unit_price_incl_tax:
            return 0
        return self.unit_price_excl_tax / self.unit_price_incl_tax

    # ==========
    # Properties
    # ==========

    @property
    def has_discount(self):
        return self.quantity > self.quantity_without_discount

    @property
    def quantity_with_discount(self):
        return self._affected_quantity

    @property
    def quantity_without_discount(self):
        return int(self.quantity - self._affected_quantity)

    @property
    def is_available_for_discount(self):
        return self.quantity_without_discount > 0

    @property
    def discount_value(self):
        return self._discount

    @property
    def unit_price_excl_tax(self):
        """Return unit price excluding tax"""
        return self._get_stockrecord_property('price_excl_tax')

    @property
    def unit_price_incl_tax(self):
        """Return unit price including tax"""
        if not self._charge_tax:
            return self.unit_price_excl_tax
        return self._get_stockrecord_property('price_incl_tax')

    @property
    def unit_tax(self):
        """Return tax of a unit"""
        if not self._charge_tax:
            return Decimal('0.00')
        return self._get_stockrecord_property('price_tax')

    @property
    def line_price_excl_tax(self):
        """Return line price excluding tax"""
        return self.quantity * self.unit_price_excl_tax

    @property
    def line_price_excl_tax_and_discounts(self):
        return self.line_price_excl_tax - self._discount * self._tax_ratio

    @property
    def line_tax(self):
        """Return line tax"""
        return self.quantity * self.unit_tax

    @property
    def line_price_incl_tax(self):
        """Return line price including tax"""
        return self.quantity * self.unit_price_incl_tax

    @property
    def line_price_incl_tax_and_discounts(self):
        return self.line_price_incl_tax - self._discount

    @property
    def description(self):
        """Return product description"""
        d = str(self.product)
        ops = []
        for attribute in self.attributes.all():
            ops.append("%s = '%s'" % (attribute.option.name, attribute.value))
        if ops:
            d = "%s (%s)" % (d.decode('utf-8'), ", ".join(ops))
        return d

    def get_warning(self):
        """
        Return a warning message about this basket line if one is applicable

        This could be things like the price has changed
        """
        if not self.price_incl_tax:
            return
        if not self.product.has_stockrecord:
            msg = u"'%(product)s' is no longer available"
            return _(msg) % {'product': self.product.get_title()}

        current_price_incl_tax = self.product.stockrecord.price_incl_tax
        if current_price_incl_tax > self.price_incl_tax:
            msg = ("The price of '%(product)s' has increased from "
                   "%(old_price)s to %(new_price)s since you added it "
                   "to your basket")
            return _(msg) % {
                'product': self.product.get_title(),
                'old_price': currency(self.price_incl_tax),
                'new_price': currency(current_price_incl_tax)}
        if current_price_incl_tax < self.price_incl_tax:
            msg = ("The price of '%(product)s' has decreased from "
                   "%(old_price)s to %(new_price)s since you added it "
                   "to your basket")
            return _(msg) % {
                'product': self.product.get_title(),
                'old_price': currency(self.price_incl_tax),
                'new_price': currency(current_price_incl_tax)}


class AbstractLineAttribute(models.Model):
    """
    An attribute of a basket line
    """
    line = models.ForeignKey('basket.Line', related_name='attributes',
                             verbose_name=_("Line"))
    option = models.ForeignKey('catalogue.Option', verbose_name=_("Option"))
    value = models.CharField(_("Value"), max_length=255)

    class Meta:
        abstract = True
        verbose_name = _('Line attribute')
        verbose_name_plural = _('Line attributes')
