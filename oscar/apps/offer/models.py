from decimal import Decimal as D, ROUND_DOWN, ROUND_UP
import math
import datetime

from django.core import exceptions
from django.template.defaultfilters import slugify
from django.db import models
from django.utils.translation import ungettext, ugettext as _
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings

from oscar.apps.offer.managers import ActiveOfferManager
from oscar.models.fields import PositiveDecimalField, ExtendedURLField


class ConditionalOffer(models.Model):
    """
    A conditional offer (eg buy 1, get 10% off)
    """
    name = models.CharField(_("Name"), max_length=128, unique=True,
                            help_text=_("""This is displayed within the customer's
                            basket"""))
    slug = models.SlugField(_("Slug"), max_length=128, unique=True, null=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    # Offers come in a few different types:
    # (a) Offers that are available to all customers on the site.  Eg a
    #     3-for-2 offer.
    # (b) Offers that are linked to a voucher, and only become available once
    #     that voucher has been applied to the basket
    # (c) Offers that are linked to a user.  Eg, all students get 10% off.  The code
    #     to apply this offer needs to be coded
    # (d) Session offers - these are temporarily available to a user after some trigger
    #     event.  Eg, users coming from some affiliate site get 10% off.
    SITE, VOUCHER, USER, SESSION = ("Site", "Voucher", "User", "Session")
    TYPE_CHOICES = (
        (SITE, _("Site offer - available to all users")),
        (VOUCHER, _("Voucher offer - only available after entering the appropriate voucher code")),
        (USER, _("User offer - available to certain types of user")),
        (SESSION, _("Session offer - temporary offer, available for a user for the duration of their session")),
    )
    offer_type = models.CharField(_("Type"), choices=TYPE_CHOICES, default=SITE, max_length=128)

    condition = models.ForeignKey('offer.Condition', verbose_name=_("Condition"))
    benefit = models.ForeignKey('offer.Benefit', verbose_name=_("Benefit"))

    # Range of availability.  Note that if this is a voucher offer, then these
    # dates are ignored and only the dates from the voucher are used to determine
    # availability.
    start_date = models.DateField(_("Start Date"), blank=True, null=True)
    end_date = models.DateField(_("End Date"), blank=True, null=True,
                                help_text=_("Offers are not active on their end "
                                            "date, only the days preceding"))

    # Some complicated situations require offers to be applied in a set order.
    priority = models.IntegerField(_("Priority"), default=0,
        help_text=_("The highest priority offers are applied first"))

    # Use this field to limit the number of times this offer can be applied to
    # a basket.
    max_applications = models.PositiveIntegerField(
        blank=True, null=True,
        help_text=_("This controls the maximum times an offer can "
                    "be applied to a single basket"))

    # We track some information on usage
    total_discount = models.DecimalField(_("Total Discount"),
                                         decimal_places=2, max_digits=12,
                                         default=D('0.00'))
    num_orders = models.PositiveIntegerField(_("Number of Orders"), default=0)

    redirect_url = ExtendedURLField(_("URL redirect (optional)"), blank=True)

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    # We need to track the voucher that this offer came from (if it is a
    # voucher offer)
    _voucher = None

    class Meta:
        ordering = ['-priority']
        verbose_name = _("Conditional Offer")
        verbose_name_plural = _("Conditional Offers")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(ConditionalOffer, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('offer:detail', kwargs={'slug': self.slug})

    def __unicode__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise exceptions.ValidationError(_('End date should be later than start date'))

    def is_active(self, test_date=None):
        if not test_date:
            test_date = datetime.date.today()
        return self.start_date <= test_date and test_date < self.end_date

    def is_condition_satisfied(self, basket):
        return self._proxy_condition().is_satisfied(basket)

    def is_condition_partially_satisfied(self, basket):
        return self._proxy_condition().is_partially_satisfied(basket)

    def get_upsell_message(self, basket):
        return self._proxy_condition().get_upsell_message(basket)

    def apply_benefit(self, basket):
        """
        Applies the benefit to the given basket and returns the discount.
        """
        if not self.is_condition_satisfied(basket):
            return D('0.00')
        return self._proxy_benefit().apply(basket, self._proxy_condition())

    def set_voucher(self, voucher):
        self._voucher = voucher

    def get_voucher(self):
        return self._voucher

    def get_max_applications(self):
        if self.max_applications is None:
            # Default value to prevent infinite loops
            return 10000
        return self.max_applications

    def _proxy_condition(self):
        """
        Returns the appropriate proxy model for the condition
        """
        field_dict = dict(self.condition.__dict__)
        for field in field_dict.keys():
            if field.startswith('_'):
                del field_dict[field]

        klassmap = {
            self.condition.COUNT: CountCondition,
            self.condition.VALUE: ValueCondition,
            self.condition.COVERAGE: CoverageCondition}
        if self.condition.type in klassmap:
            return klassmap[self.condition.type](**field_dict)
        return self.condition

    def _proxy_benefit(self):
        """
        Returns the appropriate proxy model for the condition
        """
        field_dict = dict(self.benefit.__dict__)
        for field in field_dict.keys():
            if field.startswith('_'):
                del field_dict[field]

        klassmap = {
            self.benefit.PERCENTAGE: PercentageDiscountBenefit,
            self.benefit.FIXED: AbsoluteDiscountBenefit,
            self.benefit.MULTIBUY: MultibuyDiscountBenefit,
            self.benefit.FIXED_PRICE: FixedPriceBenefit}
        if self.benefit.type in klassmap:
            return klassmap[self.benefit.type](**field_dict)
        return self.benefit

    def record_usage(self, discount):
        self.num_orders += 1
        self.total_discount += discount
        self.save()
    record_usage.alters_data = True


class Condition(models.Model):
    COUNT, VALUE, COVERAGE = ("Count", "Value", "Coverage")
    TYPE_CHOICES = (
        (COUNT, _("Depends on number of items in basket that are in condition range")),
        (VALUE, _("Depends on value of items in basket that are in condition range")),
        (COVERAGE, _("Needs to contain a set number of DISTINCT items from the condition range"))
    )
    range = models.ForeignKey('offer.Range', verbose_name=_("Range"))
    type = models.CharField(_('Type'), max_length=128, choices=TYPE_CHOICES)
    value = PositiveDecimalField(_('Value'), decimal_places=2, max_digits=12)

    class Meta:
        verbose_name = _("Condition")
        verbose_name_plural = _("Conditions")

    def __unicode__(self):
        if self.type == self.COUNT:
            return _("Basket includes %(count)d item(s) from %(range)s") % {
                'count': self.value, 'range': unicode(self.range).lower()}
        elif self.type == self.COVERAGE:
            return _("Basket includes %(count)d distinct products from %(range)s") % {
                'count': self.value, 'range': unicode(self.range).lower()}
        return _("Basket includes %(count)d value from %(range)s") % {
                'count': self.value, 'range': unicode(self.range).lower()}

    description = __unicode__

    def consume_items(self, basket, lines):
        raise NotImplementedError("This method should never be called - "
                                  "ensure you are using the correct proxy model")

    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition.  This is
        stubbed in this top-class object.  The subclassing proxies are
        responsible for implementing it correctly.
        """
        return False

    def is_partially_satisfied(self, basket):
        """
        Determine if the basket partially meets the condition.  This is useful
        for up-selling messages to entice customers to buy something more in
        order to qualify for an offer.
        """
        return False

    def get_upsell_message(self, basket):
        return None

    def can_apply_condition(self, product):
        """
        Determines whether the condition can be applied to a given product
        """
        return (self.range.contains_product(product)
                and product.is_discountable and product.has_stockrecord)

    def get_applicable_lines(self, basket, most_expensive_first=True):
        """
        Return line data for the lines that can be consumed by this condition
        """
        line_tuples = []
        for line in basket.all_lines():
            product = line.product
            if not self.can_apply_condition(product):
                continue
            price = line.unit_price_incl_tax
            if not price:
                continue
            line_tuples.append((price, line))
        if most_expensive_first:
            return sorted(line_tuples, reverse=True)
        return sorted(line_tuples)


class Benefit(models.Model):
    PERCENTAGE, FIXED, MULTIBUY, FIXED_PRICE = ("Percentage", "Absolute", "Multibuy", "Fixed price")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a % of the product's value")),
        (FIXED, _("Discount is a fixed amount off the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free")),
        (FIXED_PRICE, _("Get the products that meet the condition for a fixed price")),
    )
    range = models.ForeignKey('offer.Range', null=True, blank=True, verbose_name=_("Range"))
    type = models.CharField(_("Type"), max_length=128, choices=TYPE_CHOICES)
    value = PositiveDecimalField(_("Value"), decimal_places=2, max_digits=12,
                                 null=True, blank=True)

    # If this is not set, then there is no upper limit on how many products
    # can be discounted by this benefit.
    max_affected_items = models.PositiveIntegerField(_("Max Affected Items"), blank=True, null=True,
        help_text=_("Set this to prevent the discount consuming all items within the range that are in the basket."))

    class Meta:
        verbose_name = _("Benefit")
        verbose_name_plural = _("Benefits")

    def __unicode__(self):
        if self.type == self.PERCENTAGE:
            desc = _("%(value)s%% discount on %(range)s") % {'value': self.value, 'range': unicode(self.range).lower()}
        elif self.type == self.MULTIBUY:
            desc = _("Cheapest product is free from %s") % unicode(self.range).lower()
        elif self.type == self.FIXED_PRICE:
            desc = _("The products that meet the condition are sold for %s") % self.value
        else:
            desc = _("%(value).2f discount on %(range)s") % {'value': float(self.value),
                                                             'range': unicode(self.range).lower()}

        if self.max_affected_items:
            desc += ungettext(" (max %d item)", " (max %d items)", self.max_affected_items) % self.max_affected_items

        return desc

    description = __unicode__

    def apply(self, basket, condition):
        return D('0.00')

    def clean(self):
        if self.value is None:
            if not self.type:
                raise ValidationError(_("Benefit requires a value"))
            elif self.type != self.MULTIBUY:
                raise ValidationError(_("Benefits of type %s need a value") % self.type)
        elif self.value > 100 and self.type == 'Percentage':
            raise ValidationError(_("Percentage benefit value can't be greater than 100"))
        # All benefits need a range apart from FIXED_PRICE
        if self.type and self.type != self.FIXED_PRICE and not self.range:
            raise ValidationError(_("Benefits of type %s need a range") % self.type)

    def round(self, amount):
        """
        Apply rounding to discount amount
        """
        if hasattr(settings, 'OSCAR_OFFER_ROUNDING_FUNCTION'):
            return settings.OSCAR_OFFER_ROUNDING_FUNCTION(amount)
        return amount.quantize(D('.01'), ROUND_DOWN)

    def _effective_max_affected_items(self):
        """
        Return the maximum number of items that can have a discount applied
        during the application of this benefit
        """
        return self.max_affected_items if self.max_affected_items else 10000

    def can_apply_benefit(self, product):
        """
        Determines whether the benefit can be applied to a given product
        """
        return product.has_stockrecord and product.is_discountable

    def get_applicable_lines(self, basket, range=None):
        """
        Return the basket lines that are available to be discounted

        :basket: The basket
        :range: The range of products to use for filtering.  The fixed-price
        benefit ignores its range and uses the condition range
        """
        if range is None:
            range = self.range
        line_tuples = []
        for line in basket.all_lines():
            product = line.product
            if (not range.contains(product) or
                not self.can_apply_benefit(product)):
                continue
            price = line.unit_price_incl_tax
            if not price:
                # Avoid zero price products
                continue
            if line.quantity_without_discount == 0:
                continue
            line_tuples.append((price, line))

        # We sort lines to be cheapest first to ensure consistent applications
        return sorted(line_tuples)


class Range(models.Model):
    """
    Represents a range of products that can be used within an offer
    """
    name = models.CharField(_("Name"), max_length=128, unique=True)
    includes_all_products = models.BooleanField(_('Includes All Products'), default=False)
    included_products = models.ManyToManyField('catalogue.Product', related_name='includes', blank=True,
        verbose_name=_("Included Products"))
    excluded_products = models.ManyToManyField('catalogue.Product', related_name='excludes', blank=True,
        verbose_name=_("Excluded Products"))
    classes = models.ManyToManyField('catalogue.ProductClass', related_name='classes', blank=True,
        verbose_name=_("Product Classes"))
    included_categories = models.ManyToManyField('catalogue.Category', related_name='includes', blank=True,
        verbose_name=_("Included Categories"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    __included_product_ids = None
    __excluded_product_ids = None
    __class_ids = None

    class Meta:
        verbose_name = _("Range")
        verbose_name_plural = _("Ranges")

    def __unicode__(self):
        return self.name

    def contains_product(self, product):
        """
        Check whether the passed product is part of this range
        """
        # We look for shortcircuit checks first before
        # the tests that require more database queries.

        if settings.OSCAR_OFFER_BLACKLIST_PRODUCT and \
            settings.OSCAR_OFFER_BLACKLIST_PRODUCT(product):
            return False
        excluded_product_ids = self._excluded_product_ids()
        if product.id in excluded_product_ids:
            return False
        if self.includes_all_products:
            return True
        if product.product_class_id in self._class_ids():
            return True
        included_product_ids = self._included_product_ids()
        if product.id in included_product_ids:
            return True
        test_categories = self.included_categories.all()
        if test_categories:
            for category in product.categories.all():
                for test_category in test_categories:
                    if category == test_category or category.is_descendant_of(test_category):
                        return True
        return False

    # Shorter alias
    contains = contains_product

    def _included_product_ids(self):
        if None == self.__included_product_ids:
            self.__included_product_ids = [row['id'] for row in self.included_products.values('id')]
        return self.__included_product_ids

    def _excluded_product_ids(self):
        if None == self.__excluded_product_ids:
            self.__excluded_product_ids = [row['id'] for row in self.excluded_products.values('id')]
        return self.__excluded_product_ids

    def _class_ids(self):
        if None == self.__class_ids:
            self.__class_ids = [row['id'] for row in self.classes.values('id')]
        return self.__class_ids

    def num_products(self):
        if self.includes_all_products:
            return None
        return self.included_products.all().count()

# ==========
# Conditions
# ==========

class CountCondition(Condition):
    """
    An offer condition dependent on the NUMBER of matching items from the basket.
    """

    class Meta:
        proxy = True
        verbose_name = _("Count Condition")
        verbose_name_plural = _("Count Conditions")

    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition
        """
        num_matches = 0
        for line in basket.all_lines():
            if (self.can_apply_condition(line.product)
                and line.quantity_without_discount > 0):
                num_matches += line.quantity_without_discount
            if num_matches >= self.value:
                return True
        return False

    def _get_num_matches(self, basket):
        if hasattr(self, '_num_matches'):
            return getattr(self, '_num_matches')
        num_matches = 0
        for line in basket.all_lines():
            if (self.can_apply_condition(line.product)
                and line.quantity_without_discount > 0):
                num_matches += line.quantity_without_discount
        self._num_matches = num_matches
        return num_matches

    def is_partially_satisfied(self, basket):
        num_matches = self._get_num_matches(basket)
        return 0 < num_matches < self.value

    def get_upsell_message(self, basket):
        num_matches = self._get_num_matches(basket)
        delta = self.value - num_matches
        return ungettext('Buy %(delta)d more product from %(range)s',
                         'Buy %(delta)d more products from %(range)s', delta) % {
                            'delta': delta, 'range': self.range}

    def consume_items(self, basket, affected_lines):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.

        :basket: The basket
        :affected_lines: The lines that have been affected by the discount.
        This should be list of tuples (line, discount, qty)
        """
        # We need to count how many items have already been consumed as part of
        # applying the benefit, so we don't consume too many items.
        num_consumed = 0
        for line, __, quantity in affected_lines:
            num_consumed += quantity
        to_consume = max(0, self.value - num_consumed)
        if to_consume == 0:
            return

        for __, line in self.get_applicable_lines(basket,
                                                  most_expensive_first=True):
            quantity_to_consume = min(line.quantity_without_discount,
                                      to_consume)
            line.consume(quantity_to_consume)
            to_consume -= quantity_to_consume
            if to_consume == 0:
                break


class CoverageCondition(Condition):
    """
    An offer condition dependent on the number of DISTINCT matching items from the basket.
    """
    class Meta:
        proxy = True
        verbose_name = _("Coverage Condition")
        verbose_name_plural = _("Coverage Conditions")


    def is_satisfied(self, basket):
        """
        Determines whether a given basket meets this condition
        """
        covered_ids = []
        for line in basket.all_lines():
            if not line.is_available_for_discount:
                continue
            product = line.product
            if (self.can_apply_condition(product) and product.id not in covered_ids):
                covered_ids.append(product.id)
            if len(covered_ids) >= self.value:
                return True
        return False

    def _get_num_covered_products(self, basket):
        covered_ids = []
        for line in basket.all_lines():
            if not line.is_available_for_discount:
                continue
            product = line.product
            if (self.can_apply_condition(product) and product.id not in covered_ids):
                covered_ids.append(product.id)
        return len(covered_ids)

    def get_upsell_message(self, basket):
        delta = self.value - self._get_num_covered_products(basket)
        return ungettext('Buy %(delta)d more product from %(range)s',
                         'Buy %(delta)d more products from %(range)s', delta) % {
                         'delta': delta, 'range': self.range}

    def is_partially_satisfied(self, basket):
        return 0 < self._get_num_covered_products(basket) < self.value

    def consume_items(self, basket, affected_lines):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.
        """
        # Determine products that have already been consumed by applying the
        # benefit
        consumed_products = []
        for line, __, quantity in affected_lines:
            consumed_products.append(line.product)

        to_consume = max(0, self.value - len(consumed_products))
        if to_consume == 0:
            return

        for line in basket.all_lines():
            product = line.product
            if not self.can_apply_condition(product):
                continue
            if product in consumed_products:
                continue
            if not line.is_available_for_discount:
                continue
            # Only consume a quantity of 1 from each line
            line.consume(1)
            consumed_products.append(product)
            to_consume -= 1
            if to_consume == 0:
                break

    def get_value_of_satisfying_items(self, basket):
        covered_ids = []
        value = D('0.00')
        for line in basket.all_lines():
            if (self.can_apply_condition(line.product) and line.product.id not in covered_ids):
                covered_ids.append(line.product.id)
                value += line.unit_price_incl_tax
            if len(covered_ids) >= self.value:
                return value
        return value


class ValueCondition(Condition):
    """
    An offer condition dependent on the VALUE of matching items from the
    basket.
    """

    class Meta:
        proxy = True
        verbose_name = _("Value Condition")
        verbose_name_plural = _("Value Conditions")

    def is_satisfied(self, basket):
        """
        Determine whether a given basket meets this condition
        """
        value_of_matches = D('0.00')
        for line in basket.all_lines():
            product = line.product
            if (self.can_apply_condition(product) and product.has_stockrecord
                and line.quantity_without_discount > 0):
                price = line.unit_price_incl_tax
                value_of_matches += price * int(line.quantity_without_discount)
            if value_of_matches >= self.value:
                return True
        return False

    def _get_value_of_matches(self, basket):
        if hasattr(self, '_value_of_matches'):
            return getattr(self, '_value_of_matches')
        value_of_matches = D('0.00')
        for line in basket.all_lines():
            product = line.product
            if (self.can_apply_condition(product) and product.has_stockrecord
                and line.quantity_without_discount > 0):
                price = line.unit_price_incl_tax
                value_of_matches += price * int(line.quantity_without_discount)
        self._value_of_matches = value_of_matches
        return value_of_matches

    def is_partially_satisfied(self, basket):
        value_of_matches = self._get_value_of_matches(basket)
        return D('0.00') < value_of_matches < self.value

    def get_upsell_message(self, basket):
        value_of_matches = self._get_value_of_matches(basket)
        return _('Spend %(value)s more from %(range)s') % {'value': value_of_matches, 'range': self.range}

    def consume_items(self, basket, affected_lines):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.

        We allow lines to be passed in as sometimes we want them sorted
        in a specific order.
        """
        # Determine value of items already consumed as part of discount
        value_consumed = D('0.00')
        for line, __, qty in affected_lines:
            price = line.unit_price_incl_tax
            value_consumed += price * qty

        to_consume = max(0, self.value - value_consumed)
        if to_consume == 0:
            return

        for price, line in self.get_applicable_lines(basket,
                                                     most_expensive_first=True):
            quantity_to_consume = min(
                line.quantity_without_discount,
                (to_consume / price).quantize(D(1), ROUND_UP))
            line.consume(quantity_to_consume)
            to_consume -= price * quantity_to_consume
            if to_consume == 0:
                break

# ========
# Benefits
# ========


class PercentageDiscountBenefit(Benefit):
    """
    An offer benefit that gives a percentage discount
    """

    class Meta:
        proxy = True
        verbose_name = _("Percentage discount benefit")
        verbose_name_plural = _("Percentage discount benefits")

    def apply(self, basket, condition):
        line_tuples = self.get_applicable_lines(basket)

        discount = D('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()
        affected_lines = []
        for price, line in line_tuples:
            if affected_items >= max_affected_items:
                break
            quantity_affected = min(line.quantity_without_discount,
                                    max_affected_items - affected_items)
            line_discount = self.round(self.value / D('100.0') * price
                                        * int(quantity_affected))
            line.discount(line_discount, quantity_affected)

            affected_lines.append((line, line_discount, quantity_affected))
            affected_items += quantity_affected
            discount += line_discount

        if discount > 0:
            condition.consume_items(basket, affected_lines)
        return discount


class AbsoluteDiscountBenefit(Benefit):
    """
    An offer benefit that gives an absolute discount
    """

    class Meta:
        proxy = True
        verbose_name = _("Absolute discount benefit")
        verbose_name_plural = _("Absolute discount benefits")

    def apply(self, basket, condition):
        line_tuples = self.get_applicable_lines(basket)
        if not line_tuples:
            return self.round(D('0.00'))

        discount = D('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()
        affected_lines = []
        for price, line in line_tuples:
            if affected_items >= max_affected_items:
                break
            remaining_discount = self.value - discount
            quantity_affected = min(
                line.quantity_without_discount,
                max_affected_items - affected_items,
                int(math.ceil(remaining_discount / price)))
            line_discount = self.round(min(remaining_discount,
                                            quantity_affected * price))
            line.discount(line_discount, quantity_affected)

            affected_lines.append((line, line_discount, quantity_affected))
            affected_items += quantity_affected
            discount += line_discount

        if discount > 0:
            condition.consume_items(basket, affected_lines)

        return discount


class FixedPriceBenefit(Benefit):
    """
    An offer benefit that gives the items in the condition for a
    fixed price.  This is useful for "bundle" offers.

    Note that we ignore the benefit range here and only give a fixed price
    for the products in the condition range.  The condition cannot be a value
    condition.

    We also ignore the max_affected_items setting.
    """
    class Meta:
        proxy = True
        verbose_name = _("Fixed price benefit")
        verbose_name_plural = _("Fixed price benefits")

    def apply(self, basket, condition):
        if isinstance(condition, ValueCondition):
            return self.round(D('0.00'))

        line_tuples = self.get_applicable_lines(basket, range=condition.range)
        if not line_tuples:
            return self.round(D('0.00'))

        # Determine the lines to consume
        num_permitted = int(condition.value)
        num_affected = 0
        value_affected = D('0.00')
        covered_lines = []
        for price, line in line_tuples:
            if isinstance(condition, CoverageCondition):
                quantity_affected = 1
            else:
                quantity_affected = min(
                    line.quantity_without_discount,
                    num_permitted - num_affected)
            num_affected += quantity_affected
            value_affected += quantity_affected * price
            covered_lines.append((price, line, quantity_affected))
            if num_affected >= num_permitted:
                break
        discount = max(value_affected - self.value, D('0.00'))
        if not discount:
            return self.round(discount)

        # Apply discount to the affected lines
        discount_applied = D('0.00')
        last_line = covered_lines[-1][0]
        for price, line, quantity in covered_lines:
            if line == last_line:
                # If last line, we just take the difference to ensure that
                # rounding doesn't lead to an off-by-one error
                line_discount = discount - discount_applied
            else:
                line_discount = self.round(
                    discount * (price * quantity) / value_affected)
            line.discount(line_discount, quantity)
            discount_applied += line_discount
        return discount


class MultibuyDiscountBenefit(Benefit):

    class Meta:
        proxy = True
        verbose_name = _("Multibuy discount benefit")
        verbose_name_plural = _("Multibuy discount benefits")

    def apply(self, basket, condition):
        line_tuples = self.get_applicable_lines(basket)
        if not line_tuples:
            return self.round(D('0.00'))

        # Cheapest line gives free product
        discount, line = line_tuples[0]
        line.discount(discount, 1)

        affected_lines = [(line, discount, 1)]
        condition.consume_items(basket, affected_lines)

        return discount
