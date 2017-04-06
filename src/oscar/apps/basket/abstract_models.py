import zlib
from decimal import Decimal as D

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import models
from django.db.models import Sum
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from oscar.apps.basket.managers import OpenBasketManager, SavedBasketManager
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import get_class
from oscar.core.utils import get_default_currency
from oscar.models.fields.slugfield import SlugField
from oscar.templatetags.currency_filters import currency

OfferApplications = get_class('offer.results', 'OfferApplications')
Unavailable = get_class('partner.availability', 'Unavailable')
LineOfferConsumer = get_class('basket.utils', 'LineOfferConsumer')


@python_2_unicode_compatible
class AbstractBasket(models.Model):
    """
    Basket object
    """
    # Baskets can be anonymously owned - hence this field is nullable.  When a
    # anon user signs in, their two baskets are merged.
    owner = models.ForeignKey(
        AUTH_USER_MODEL,
        null=True,
        related_name='baskets',
        on_delete=models.CASCADE,
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
        'voucher.Voucher', verbose_name=_("Vouchers"), blank=True)

    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_merged = models.DateTimeField(_("Date merged"), null=True, blank=True)
    date_submitted = models.DateTimeField(_("Date submitted"), null=True,
                                          blank=True)

    # Only if a basket is in one of these statuses can it be edited
    editable_statuses = (OPEN, SAVED)

    class Meta:
        abstract = True
        app_label = 'basket'
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
        self._lines = None
        self.offer_applications = OfferApplications()

    def __str__(self):
        return _(
            u"%(status)s basket (owner: %(owner)s, lines: %(num_lines)d)") \
            % {'status': self.status,
               'owner': self.owner,
               'num_lines': self.num_lines}

    # ========
    # Strategy
    # ========

    @property
    def has_strategy(self):
        return hasattr(self, '_strategy')

    def _get_strategy(self):
        if not self.has_strategy:
            raise RuntimeError(
                "No strategy class has been assigned to this basket. "
                "This is normally assigned to the incoming request in "
                "oscar.apps.basket.middleware.BasketMiddleware. "
                "Since it is missing, you must be doing something different. "
                "Ensure that a strategy instance is assigned to the basket!"
            )
        return self._strategy

    def _set_strategy(self, strategy):
        self._strategy = strategy

    strategy = property(_get_strategy, _set_strategy)

    def all_lines(self):
        """
        Return a cached set of basket lines.

        This is important for offers as they alter the line models and you
        don't want to reload them from the DB as that information would be
        lost.
        """
        if self.id is None:
            return self.lines.none()
        if self._lines is None:
            self._lines = (
                self.lines
                .select_related('product', 'stockrecord')
                .prefetch_related(
                    'attributes', 'product__images')
                .order_by(self._meta.pk.name))
        return self._lines

    def is_quantity_allowed(self, qty):
        """
        Test whether the passed quantity of items can be added to the basket
        """
        # We enforce a max threshold to prevent a DOS attack via the offers
        # system.
        basket_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.num_items
            max_allowed = basket_threshold - total_basket_quantity
            if qty > max_allowed:
                return False, _(
                    "Due to technical limitations we are not able "
                    "to ship more than %(threshold)d items in one order.") \
                    % {'threshold': basket_threshold}
        return True, None

    # ============
    # Manipulation
    # ============

    def flush(self):
        """
        Remove all lines from basket.
        """
        if self.status == self.FROZEN:
            raise PermissionDenied("A frozen basket cannot be flushed")
        self.lines.all().delete()
        self._lines = None

    def add_product(self, product, quantity=1, options=None):
        """
        Add a product to the basket

        'stock_info' is the price and availability data returned from
        a partner strategy class.

        The 'options' list should contains dicts with keys 'option' and 'value'
        which link the relevant product.Option model and string value
        respectively.

        Returns (line, created).
          line: the matching basket line
          created: whether the line was created or updated

        """
        if options is None:
            options = []
        if not self.id:
            self.save()

        # Ensure that all lines are the same currency
        price_currency = self.currency
        stock_info = self.strategy.fetch_for_product(product)
        if price_currency and stock_info.price.currency != price_currency:
            raise ValueError((
                "Basket lines must all have the same currency. Proposed "
                "line has currency %s, while basket has currency %s")
                % (stock_info.price.currency, price_currency))

        if stock_info.stockrecord is None:
            raise ValueError((
                "Basket lines must all have stock records. Strategy hasn't "
                "found any stock record for product %s") % product)

        # Line reference is used to distinguish between variations of the same
        # product (eg T-shirts with different personalisations)
        line_ref = self._create_line_reference(
            product, stock_info.stockrecord, options)

        # Determine price to store (if one exists).  It is only stored for
        # audit and sometimes caching.
        defaults = {
            'quantity': quantity,
            'price_excl_tax': stock_info.price.excl_tax,
            'price_currency': stock_info.price.currency,
        }
        if stock_info.price.is_tax_known:
            defaults['price_incl_tax'] = stock_info.price.incl_tax

        line, created = self.lines.get_or_create(
            line_reference=line_ref,
            product=product,
            stockrecord=stock_info.stockrecord,
            defaults=defaults)
        if created:
            for option_dict in options:
                line.attributes.create(option=option_dict['option'],
                                       value=option_dict['value'])
        else:
            line.quantity = max(0, line.quantity + quantity)
            line.save()
        self.reset_offer_applications()

        # Returning the line is useful when overriding this method.
        return line, created
    add_product.alters_data = True
    add = add_product

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
        self.offer_applications = OfferApplications()
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
        # Use basket.lines.all instead of all_lines as this function is called
        # before a strategy has been assigned.
        for line_to_merge in basket.lines.all():
            self.merge_line(line_to_merge, add_quantities)
        basket.status = self.MERGED
        basket.date_merged = now()
        basket._lines = None
        basket.save()
        # Ensure all vouchers are moved to the new basket
        for voucher in basket.vouchers.all():
            basket.vouchers.remove(voucher)
            self.vouchers.add(voucher)
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

    def _create_line_reference(self, product, stockrecord, options):
        """
        Returns a reference string for a line based on the item
        and its options.
        """
        base = '%s_%s' % (product.id, stockrecord.id)
        if not options:
            return base
        repr_options = [{'option': repr(option['option']),
                         'value': repr(option['value'])} for option in options]
        return "%s_%s" % (base, zlib.crc32(repr(repr_options).encode('utf8')))

    def _get_total(self, property):
        """
        For executing a named method on each line of the basket
        and returning the total.
        """
        total = D('0.00')
        for line in self.all_lines():
            try:
                total += getattr(line, property)
            except ObjectDoesNotExist:
                # Handle situation where the product may have been deleted
                pass
            except TypeError:
                # Handle Unavailable products with no known price
                info = self.strategy.fetch_for_product(line.product)
                if info.availability.is_available_to_buy:
                    raise
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
    def is_tax_known(self):
        """
        Test if tax values are known for this basket
        """
        return all([line.is_tax_known for line in self.all_lines()])

    @property
    def total_excl_tax(self):
        """
        Return total line price excluding tax
        """
        return self._get_total('line_price_excl_tax_incl_discounts')

    @property
    def total_tax(self):
        """Return total tax for a line"""
        return self._get_total('line_tax')

    @property
    def total_incl_tax(self):
        """
        Return total price inclusive of tax and discounts
        """
        return self._get_total('line_price_incl_tax_incl_discounts')

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
    def has_shipping_discounts(self):
        return len(self.shipping_discounts) > 0

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
        return self.all_lines().count()

    @property
    def num_items(self):
        """Return number of items"""
        return sum(line.quantity for line in self.lines.all())

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
        if not self.id:
            return False
        return self.vouchers.exists()

    @property
    def is_submitted(self):
        return self.status == self.SUBMITTED

    @property
    def can_be_edited(self):
        """
        Test if a basket can be edited
        """
        return self.status in self.editable_statuses

    @property
    def currency(self):
        # Since all lines should have the same currency, return the currency of
        # the first one found.
        for line in self.all_lines():
            return line.price_currency

    # =============
    # Query methods
    # =============

    def contains_voucher(self, code):
        """
        Test whether the basket contains a voucher with a given code
        """
        if self.id is None:
            return False
        try:
            self.vouchers.get(code=code)
        except ObjectDoesNotExist:
            return False
        else:
            return True

    def product_quantity(self, product):
        """
        Return the quantity of a product in the basket

        The basket can contain multiple lines with the same product, but
        different options and stockrecords. Those quantities are summed up.
        """
        matching_lines = self.lines.filter(product=product)
        quantity = matching_lines.aggregate(Sum('quantity'))['quantity__sum']
        return quantity or 0

    def line_quantity(self, product, stockrecord, options=None):
        """
        Return the current quantity of a specific product and options
        """
        ref = self._create_line_reference(product, stockrecord, options)
        try:
            return self.lines.get(line_reference=ref).quantity
        except ObjectDoesNotExist:
            return 0


@python_2_unicode_compatible
class AbstractLine(models.Model):
    """A line of a basket (product and a quantity)

    Common approaches on ordering basket lines:

        a) First added at top. That's the history-like approach; new items are
           added to the bottom of the list. Changing quantities doesn't impact
           position.
           Oscar does this by default. It just sorts by Line.pk, which is
           guaranteed to increment after each creation.

        b) Last modified at top. That means items move to the top when you add
           another one, and new items are added to the top as well.  Amazon
           mostly does this, but doesn't change the position when you update
           the quantity in the basket view.
           To get this behaviour, add a date_updated field, change
           Meta.ordering and optionally do something similar on wishlist lines.
           Order lines should already be created in the order of the basket
           lines, and are sorted by their primary key, so no changes should be
           necessary there.

    """
    basket = models.ForeignKey(
        'basket.Basket',
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_("Basket"))

    # This is to determine which products belong to the same line
    # We can't just use product.id as you can have customised products
    # which should be treated as separate lines.  Set as a
    # SlugField as it is included in the path for certain views.
    line_reference = SlugField(
        _("Line Reference"), max_length=128, db_index=True)

    product = models.ForeignKey(
        'catalogue.Product',
        on_delete=models.CASCADE,
        related_name='basket_lines',
        verbose_name=_("Product"))

    # We store the stockrecord that should be used to fulfil this line.
    stockrecord = models.ForeignKey(
        'partner.StockRecord',
        on_delete=models.CASCADE,
        related_name='basket_lines')

    quantity = models.PositiveIntegerField(_('Quantity'), default=1)

    # We store the unit price incl tax of the product when it is first added to
    # the basket.  This allows us to tell if a product has changed price since
    # a person first added it to their basket.
    price_currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency)
    price_excl_tax = models.DecimalField(
        _('Price excl. Tax'), decimal_places=2, max_digits=12,
        null=True)
    price_incl_tax = models.DecimalField(
        _('Price incl. Tax'), decimal_places=2, max_digits=12, null=True)

    # Track date of first addition
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super(AbstractLine, self).__init__(*args, **kwargs)
        # Instance variables used to persist discount information
        self._discount_excl_tax = D('0.00')
        self._discount_incl_tax = D('0.00')
        self.consumer = LineOfferConsumer(self)

    class Meta:
        abstract = True
        app_label = 'basket'
        # Enforce sorting by order of creation.
        ordering = ['date_created', 'pk']
        unique_together = ("basket", "line_reference")
        verbose_name = _('Basket line')
        verbose_name_plural = _('Basket lines')

    def __str__(self):
        return _(
            u"Basket #%(basket_id)d, Product #%(product_id)d, quantity"
            u" %(quantity)d") % {'basket_id': self.basket.pk,
                                 'product_id': self.product.pk,
                                 'quantity': self.quantity}

    def save(self, *args, **kwargs):
        if not self.basket.can_be_edited:
            raise PermissionDenied(
                _("You cannot modify a %s basket") % (
                    self.basket.status.lower(),))
        return super(AbstractLine, self).save(*args, **kwargs)

    # =============
    # Offer methods
    # =============

    def clear_discount(self):
        """
        Remove any discounts from this line.
        """
        self._discount_excl_tax = D('0.00')
        self._discount_incl_tax = D('0.00')
        self.consumer = LineOfferConsumer(self)

    def discount(self, discount_value, affected_quantity, incl_tax=True,
                 offer=None):
        """
        Apply a discount to this line
        """
        if incl_tax:
            if self._discount_excl_tax > 0:
                raise RuntimeError(
                    "Attempting to discount the tax-inclusive price of a line "
                    "when tax-exclusive discounts are already applied")
            self._discount_incl_tax += discount_value
        else:
            if self._discount_incl_tax > 0:
                raise RuntimeError(
                    "Attempting to discount the tax-exclusive price of a line "
                    "when tax-inclusive discounts are already applied")
            self._discount_excl_tax += discount_value
        self.consume(affected_quantity, offer=offer)

    def consume(self, quantity, offer=None):
        """
        Mark all or part of the line as 'consumed'

        Consumed items are no longer available to be used in offers.
        """
        self.consumer.consume(quantity, offer=offer)

    def get_price_breakdown(self):
        """
        Return a breakdown of line prices after discounts have been applied.

        Returns a list of (unit_price_incl_tax, unit_price_excl_tax, quantity)
        tuples.
        """
        if not self.is_tax_known:
            raise RuntimeError("A price breakdown can only be determined "
                               "when taxes are known")
        prices = []
        if not self.discount_value:
            prices.append((self.unit_price_incl_tax, self.unit_price_excl_tax,
                           self.quantity))
        else:
            # Need to split the discount among the affected quantity
            # of products.
            item_incl_tax_discount = (
                self.discount_value / int(self.consumer.consumed()))
            item_excl_tax_discount = item_incl_tax_discount * self._tax_ratio
            item_excl_tax_discount = item_excl_tax_discount.quantize(D('0.01'))
            prices.append((self.unit_price_incl_tax - item_incl_tax_discount,
                           self.unit_price_excl_tax - item_excl_tax_discount,
                           self.consumer.consumed()))
            if self.quantity_without_discount:
                prices.append((self.unit_price_incl_tax,
                               self.unit_price_excl_tax,
                               self.quantity_without_discount))
        return prices

    # =======
    # Helpers
    # =======

    @property
    def _tax_ratio(self):
        if not self.unit_price_incl_tax:
            return 0
        return self.unit_price_excl_tax / self.unit_price_incl_tax

    # ===============
    # Offer Discounts
    # ===============

    def has_offer_discount(self, offer):
        return self.consumer.consumed(offer) > 0

    def quantity_with_offer_discount(self, offer):
        return self.consumer.consumed(offer)

    def quantity_without_offer_discount(self, offer):
        return self.consumer.available(offer)

    def is_available_for_offer_discount(self, offer):
        return self.consumer.available(offer) > 0

    # ==========
    # Properties
    # ==========

    @property
    def has_discount(self):
        return bool(self.consumer.consumed())

    @property
    def quantity_with_discount(self):
        return self.consumer.consumed()

    @property
    def quantity_without_discount(self):
        return self.consumer.available()

    @property
    def is_available_for_discount(self):
        # deprecated
        return self.consumer.available() > 0

    @property
    def discount_value(self):
        # Only one of the incl- and excl- discounts should be non-zero
        return max(self._discount_incl_tax, self._discount_excl_tax)

    @property
    def purchase_info(self):
        """
        Return the stock/price info
        """
        if not hasattr(self, '_info'):
            # Cache the PurchaseInfo instance.
            self._info = self.basket.strategy.fetch_for_line(
                self, self.stockrecord)
        return self._info

    @property
    def is_tax_known(self):
        return self.purchase_info.price.is_tax_known

    @property
    def unit_effective_price(self):
        """
        The price to use for offer calculations
        """
        return self.purchase_info.price.effective_price

    @property
    def unit_price_excl_tax(self):
        return self.purchase_info.price.excl_tax

    @property
    def unit_price_incl_tax(self):
        return self.purchase_info.price.incl_tax

    @property
    def unit_tax(self):
        return self.purchase_info.price.tax

    @property
    def line_price_excl_tax(self):
        if self.unit_price_excl_tax is not None:
            return self.quantity * self.unit_price_excl_tax

    @property
    def line_price_excl_tax_incl_discounts(self):
        if self._discount_excl_tax and self.line_price_excl_tax is not None:
            return self.line_price_excl_tax - self._discount_excl_tax
        if self._discount_incl_tax and self.line_price_incl_tax is not None:
            # This is a tricky situation.  We know the discount as calculated
            # against tax inclusive prices but we need to guess how much of the
            # discount applies to tax-exclusive prices.  We do this by
            # assuming a linear tax and scaling down the original discount.
            return self.line_price_excl_tax \
                - self._tax_ratio * self._discount_incl_tax
        return self.line_price_excl_tax

    @property
    def line_price_incl_tax_incl_discounts(self):
        # We use whichever discount value is set.  If the discount value was
        # calculated against the tax-exclusive prices, then the line price
        # including tax
        if self.line_price_incl_tax is not None:
            return self.line_price_incl_tax - self.discount_value

    @property
    def line_tax(self):
        if self.is_tax_known:
            return self.quantity * self.unit_tax

    @property
    def line_price_incl_tax(self):
        if self.unit_price_incl_tax is not None:
            return self.quantity * self.unit_price_incl_tax

    @property
    def description(self):
        d = smart_text(self.product)
        ops = []
        for attribute in self.attributes.all():
            ops.append("%s = '%s'" % (attribute.option.name, attribute.value))
        if ops:
            d = "%s (%s)" % (d, ", ".join(ops))
        return d

    def get_warning(self):
        """
        Return a warning message about this basket line if one is applicable

        This could be things like the price has changed
        """
        if isinstance(self.purchase_info.availability, Unavailable):
            msg = u"'%(product)s' is no longer available"
            return _(msg) % {'product': self.product.get_title()}

        if not self.price_incl_tax:
            return
        if not self.purchase_info.price.is_tax_known:
            return

        # Compare current price to price when added to basket
        current_price_incl_tax = self.purchase_info.price.incl_tax
        if current_price_incl_tax != self.price_incl_tax:
            product_prices = {
                'product': self.product.get_title(),
                'old_price': currency(self.price_incl_tax),
                'new_price': currency(current_price_incl_tax)
            }
            if current_price_incl_tax > self.price_incl_tax:
                warning = _("The price of '%(product)s' has increased from"
                            " %(old_price)s to %(new_price)s since you added"
                            " it to your basket")
                return warning % product_prices
            else:
                warning = _("The price of '%(product)s' has decreased from"
                            " %(old_price)s to %(new_price)s since you added"
                            " it to your basket")
                return warning % product_prices


class AbstractLineAttribute(models.Model):
    """
    An attribute of a basket line
    """
    line = models.ForeignKey(
        'basket.Line',
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name=_("Line"))
    option = models.ForeignKey(
        'catalogue.Option',
        on_delete=models.CASCADE,
        verbose_name=_("Option"))
    value = models.CharField(_("Value"), max_length=255)

    class Meta:
        abstract = True
        app_label = 'basket'
        verbose_name = _('Line attribute')
        verbose_name_plural = _('Line attributes')
