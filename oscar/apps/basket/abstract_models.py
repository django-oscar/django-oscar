from decimal import Decimal
import zlib
import datetime

from django.db import models
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from oscar.apps.basket.managers import OpenBasketManager, SavedBasketManager

# Basket statuses
# - Frozen is for when a basket is in the process of being submitted
#   and we need to prevent any changes to it.
OPEN, MERGED, SAVED, FROZEN, SUBMITTED = ("Open", "Merged", "Saved", "Frozen", "Submitted")


class AbstractBasket(models.Model):
    """
    Basket object
    """
    # Baskets can be anonymously owned (which are merged if the user signs in)
    owner = models.ForeignKey('auth.User', related_name='baskets', null=True)
    STATUS_CHOICES = (
        (OPEN, _("Open - currently active")),
        (MERGED, _("Merged - superceded by another basket")),
        (SAVED, _("Saved - for items to be purchased later")),
        (FROZEN, _("Frozen - the basket cannot be modified")),
        (SUBMITTED, _("Submitted - has been ordered at the checkout")),
    )
    status = models.CharField(_("Status"), max_length=128, default=OPEN, choices=STATUS_CHOICES)
    vouchers = models.ManyToManyField('voucher.Voucher', null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_merged = models.DateTimeField(null=True, blank=True)
    date_submitted = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    objects = models.Manager()
    open = OpenBasketManager()
    saved = SavedBasketManager()

    def __init__(self, *args, **kwargs):
        super(AbstractBasket, self).__init__(*args, **kwargs)
        self._lines = None  # Cached queryset of lines
        self.discounts = None  # Dictionary of discounts
        self.exempt_from_tax = False

    def __unicode__(self):
        return u"%s basket (owner: %s, lines: %d)" % (self.status, self.owner, self.num_lines)

    def all_lines(self):
        """
        Return a cached set of basket lines.

        This is important for offers as they alter the line models and you don't
        want to reload them from the DB.
        """
        if self._lines is None:
            self._lines = self.lines.all()
        return self._lines

    # ============
    # Manipulation
    # ============

    def flush(self):
        """Remove all lines from basket."""
        if self.status == FROZEN:
            raise PermissionDenied("A frozen basket cannot be flushed")
        self.lines_all().delete()
        self._lines = None

    def add_product(self, item, quantity=1, options=None):
        """
        Convenience method for adding products to a basket

        The 'options' list should contains dicts with keys 'option' and 'value'
        which link the relevant product.Option model and string value respectively.
        """
        if options is None:
            options = []
        if not self.id:
            self.save()
        line_ref = self._create_line_reference(item, options)
        line, created = self.lines.get_or_create(line_reference=line_ref,
                                                 product=item,
                                                 defaults={'quantity': quantity})
        if created:
            for option_dict in options:
                line.attributes.create(option=option_dict['option'],
                                       value=option_dict['value'])
        else:
            line.quantity += quantity
            line.save()
        self._lines = None

    def get_discounts(self):
        if self.discounts is None:
            self.discounts = []
        return self.discounts

    def set_discounts(self, discounts):
        """
        Sets the discounts that apply to this basket.

        This should be a list of dictionaries
        """
        self.discounts = discounts

    def remove_discounts(self):
        """
        Remove any discounts so they get recalculated
        """
        self.discounts = []
        self._lines = None

    def merge_line(self, line):
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
            # Line already exists - bump its quantity and delete the old
            existing_line.quantity += line.quantity
            existing_line.save()
            line.delete()

    def merge(self, basket):
        """
        Merges another basket with this one.
        """
        for line_to_merge in basket.all_lines():
            self.merge_line(line_to_merge)
        basket.status = MERGED
        basket.date_merged = datetime.datetime.now()
        basket.save()
        self._lines = None

    def freeze(self):
        """
        Freezes the basket so it cannot be modified.
        """
        self.status = FROZEN
        self.save()

    def thaw(self):
        """
        Unfreezes a basket so it can be modified again
        """
        self.status = OPEN
        self.save()

    def set_as_submitted(self):
        """Mark this basket as submitted."""
        self.status = SUBMITTED
        self.date_submitted = datetime.datetime.now()
        self.save()

    def set_as_tax_exempt(self):
        self.exempt_from_tax = True
        for line in self.all_lines():
            line.set_as_tax_exempt()

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
        """Return bool based on basket having 0 lines"""
        return self.num_lines == 0

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
        Return discounts from non-voucher sources.
        """
        offer_discounts = []
        for discount in self.get_discounts():
            if not discount['voucher']:
                offer_discounts.append(discount)
        return offer_discounts

    @property
    def voucher_discounts(self):
        """
        Return discounts from vouchers
        """
        voucher_discounts = []
        for discount in self.get_discounts():
            if discount['voucher']:
                voucher_discounts.append(discount)
        return voucher_discounts

    @property
    def total_excl_tax_excl_discounts(self):
        """
        Return total price excluding tax and discounts
        """
        return self._get_total('line_price_excl_tax')

    @property
    def num_lines(self):
        """Return number of lines"""
        return self.all_lines().count()

    @property
    def num_items(self):
        """Return number of items"""
        return reduce(lambda num,line: num+line.quantity, self.all_lines(), 0)

    @property
    def num_items_without_discount(self):
        """Return number of items"""
        num = 0
        for line in self.all_lines():
            num += line.quantity_without_discount
        return num

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

class AbstractLine(models.Model):
    """
    A line of a basket (product and a quantity)
    """

    basket = models.ForeignKey('basket.Basket', related_name='lines')
    # This is to determine which products belong to the same line
    # We can't just use product.id as you can have customised products
    # which should be treated as separate lines.  Set as a
    # SlugField as it is included in the path for certain views.
    line_reference = models.SlugField(max_length=128, db_index=True)

    product = models.ForeignKey('catalogue.Product', related_name='basket_lines')
    quantity = models.PositiveIntegerField(default=1)

    # Track date of first addition
    date_created = models.DateTimeField(auto_now_add=True)

    # Instance variables used to persist discount information
    _discount = Decimal('0.00')
    _affected_quantity = 0
    _charge_tax = True

    class Meta:
        abstract = True
        unique_together = ("basket", "line_reference")

    def __unicode__(self):
        return u"%s, Product '%s', quantity %d" % (self.basket, self.product, self.quantity)

    def save(self, *args, **kwargs):
        """Saves a line or deletes if it's quanity is 0"""
        if self.basket.status not in (OPEN, SAVED):
            raise PermissionDenied("You cannot modify a %s basket" % self.basket.status.lower())
        if self.quantity == 0:
            return self.delete(*args, **kwargs)
        super(AbstractLine, self).save(*args, **kwargs)

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
        self._discount += discount_value
        self._affected_quantity += int(affected_quantity)

    def consume(self, quantity):
        if quantity > self.quantity - self._affected_quantity:
            inc = self.quantity - self._affected_quantity
        else:
            inc = quantity
        self._affected_quantity += int(inc)

    def get_price_breakdown(self):
        """
        Returns a breakdown of line prices after discounts have
        been applied.
        """
        prices = []
        if not self.has_discount:
            prices.append((self.unit_price_incl_tax, self.unit_price_excl_tax, self.quantity))
        else:
            # Need to split the discount among the affected quantity
            # of products.
            item_incl_tax_discount = self._discount / int(self._affected_quantity)
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


class AbstractLineAttribute(models.Model):
    """An attribute of a basket line"""
    line = models.ForeignKey('basket.Line', related_name='attributes')
    option = models.ForeignKey('catalogue.Option')
    value = models.CharField(_("Value"), max_length=255)

    class Meta:
        abstract = True


