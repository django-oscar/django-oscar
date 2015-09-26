import operator
from decimal import Decimal as D, ROUND_DOWN

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from oscar.apps.offer import results, utils
from oscar.templatetags.currency_filters import currency


__all__ = [
    'PercentageDiscountBenefit', 'AbsoluteDiscountBenefit', 'FixedPriceBenefit',
    'ShippingBenefit', 'MultibuyDiscountBenefit',
    'ShippingAbsoluteDiscountBenefit', 'ShippingFixedPriceBenefit',
    'ShippingPercentageDiscountBenefit',
]


def apply_discount(line, discount, quantity):
    """
    Apply a given discount to the passed basket
    """
    line.discount(discount, quantity, incl_tax=False)


class BenefitImplementation(object):
    def __init__(self, instance):
        self.instance = instance

    @property
    def value(self):
        return self.instance.value

    @property
    def range(self):
        return self.instance.range

    def round(self, amount):
        """
        Apply rounding to discount amount
        """
        if hasattr(settings, 'OSCAR_OFFER_ROUNDING_FUNCTION'):
            return settings.OSCAR_OFFER_ROUNDING_FUNCTION(amount)
        return amount.quantize(D('.01'), ROUND_DOWN)

    def clean(self):
        pass

    def apply(self, basket, condition, offer):
        return results.ZERO_DISCOUNT

    def apply_deferred(self, basket, order, application):
        return None

    def shipping_discount(self, charge):
        return D('0.00')

    def can_apply_benefit(self, line):
        """
        Determines whether the benefit can be applied to a given basket line
        """
        return line.stockrecord and line.product.is_discountable

    def get_applicable_lines(self, offer, basket, range=None):
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

            if not range.contains(product) or not self.can_apply_benefit(line):
                continue

            price = utils.unit_price(offer, line)
            if not price:
                # Avoid zero price products
                continue
            if line.quantity_without_discount == 0:
                continue
            line_tuples.append((price, line))

        # We sort lines to be cheapest first to ensure consistent applications
        return sorted(line_tuples, key=operator.itemgetter(0))


class PercentageDiscountBenefit(BenefitImplementation):
    """
    An offer benefit that gives a percentage discount
    """
    _description = _("%(value)s%% discount on %(range)s")
    help_text = _("Discount is a percentage off of the product's value")
    verbose_name = _("Percentage discount benefit")
    verbose_name_plural = _("Percentage discount benefits")

    @property
    def name(self):
        return self._description % {
            'value': self.value,
            'range': self.range.name}

    @property
    def description(self):
        return self._description % {
            'value': self.value,
            'range': utils.range_anchor(self.range)}

    def apply(self, basket, condition, offer, discount_percent=None,
              max_total_discount=None):
        if discount_percent is None:
            discount_percent = self.value

        discount_amount_available = max_total_discount

        line_tuples = self.get_applicable_lines(offer, basket)

        discount = D('0.00')
        affected_items = 0
        max_affected_items = self.instance._effective_max_affected_items()
        affected_lines = []
        for price, line in line_tuples:
            if affected_items >= max_affected_items:
                break
            if discount_amount_available == 0:
                break

            quantity_affected = min(line.quantity_without_discount,
                                    max_affected_items - affected_items)
            line_discount = self.round(
                discount_percent / D('100.0') * price * int(quantity_affected))

            if discount_amount_available is not None:
                line_discount = min(line_discount, discount_amount_available)
                discount_amount_available -= line_discount

            apply_discount(line, line_discount, quantity_affected)

            affected_lines.append((line, line_discount, quantity_affected))
            affected_items += quantity_affected
            discount += line_discount

        if discount > 0:
            condition.consume_items(offer, basket, affected_lines)
        return results.BasketDiscount(discount)

    def clean(self):
        if not self.instance.range:
            raise ValidationError(
                _("Percentage benefits require a product range"))
        if self.instance.value > 100:
            raise ValidationError(
                _("Percentage discount cannot be greater than 100"))


class AbsoluteDiscountBenefit(BenefitImplementation):
    """
    An offer benefit that gives an absolute discount
    """
    _description = _("%(value)s discount on %(range)s")
    help_text = _("Discount is a fixed amount off of the product's value")
    verbose_name = _("Absolute discount benefit")
    verbose_name_plural = _("Absolute discount benefits")

    @property
    def name(self):
        return self._description % {
            'value': currency(self.value),
            'range': self.range.name.lower()}

    @property
    def description(self):
        return self._description % {
            'value': currency(self.value),
            'range': utils.range_anchor(self.range)}

    def apply(self, basket, condition, offer, discount_amount=None,
              max_total_discount=None):
        if discount_amount is None:
            discount_amount = self.value

        # Fetch basket lines that are in the range and available to be used in
        # an offer.
        line_tuples = self.get_applicable_lines(offer, basket)

        # Determine which lines can have the discount applied to them
        max_affected_items = self.instance._effective_max_affected_items()
        num_affected_items = 0
        affected_items_total = D('0.00')
        lines_to_discount = []
        for price, line in line_tuples:
            if num_affected_items >= max_affected_items:
                break
            qty = min(line.quantity_without_discount,
                      max_affected_items - num_affected_items)
            lines_to_discount.append((line, price, qty))
            num_affected_items += qty
            affected_items_total += qty * price

        # Ensure we don't try to apply a discount larger than the total of the
        # matching items.
        discount = min(discount_amount, affected_items_total)
        if max_total_discount is not None:
            discount = min(discount, max_total_discount)

        if discount == 0:
            return results.ZERO_DISCOUNT

        # Apply discount equally amongst them
        affected_lines = []
        applied_discount = D('0.00')
        for i, (line, price, qty) in enumerate(lines_to_discount):
            if i == len(lines_to_discount) - 1:
                # If last line, then take the delta as the discount to ensure
                # the total discount is correct and doesn't mismatch due to
                # rounding.
                line_discount = discount - applied_discount
            else:
                # Calculate a weighted discount for the line
                line_discount = self.round(
                    ((price * qty) / affected_items_total) * discount)
            apply_discount(line, line_discount, qty)
            affected_lines.append((line, line_discount, qty))
            applied_discount += line_discount

        condition.consume_items(offer, basket, affected_lines)

        return results.BasketDiscount(discount)

    def clean(self):
        if not self.instance.range:
            raise ValidationError(
                _("Fixed discount benefits require a product range"))
        if not self.instance.value:
            raise ValidationError(
                _("Fixed discount benefits require a value"))


class FixedPriceBenefit(BenefitImplementation):
    """
    An offer benefit that gives the items in the condition for a
    fixed price.  This is useful for "bundle" offers.

    Note that we ignore the benefit range here and only give a fixed price
    for the products in the condition range.  The condition cannot be a value
    condition.

    We also ignore the max_affected_items setting.
    """
    _description = _("The products that meet the condition are sold "
                     "for %(amount)s")
    help_text = _("Get the products that meet the condition for a fixed price")
    verbose_name = _("Fixed price benefit")
    verbose_name_plural = _("Fixed price benefits")

    @property
    def name(self):
        return self._description % {
            'amount': currency(self.value)}

    def apply(self, basket, condition, offer):  # noqa (too complex (10))
        from oscar.apps.offer import conditions
        if isinstance(condition, conditions.ValueCondition):
            return results.ZERO_DISCOUNT

        # Fetch basket lines that are in the range and available to be used in
        # an offer.
        line_tuples = self.get_applicable_lines(
            offer, basket, range=condition.range)
        if not line_tuples:
            return results.ZERO_DISCOUNT

        # Determine the lines to consume
        num_permitted = int(condition.value)
        num_affected = 0
        value_affected = D('0.00')
        covered_lines = []
        for price, line in line_tuples:
            if isinstance(condition, conditions.CoverageCondition):
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
            return results.ZERO_DISCOUNT

        # Apply discount to the affected lines
        discount_applied = D('0.00')
        last_line = covered_lines[-1][1]
        for price, line, quantity in covered_lines:
            if line == last_line:
                # If last line, we just take the difference to ensure that
                # rounding doesn't lead to an off-by-one error
                line_discount = discount - discount_applied
            else:
                line_discount = self.round(
                    discount * (price * quantity) / value_affected)
            apply_discount(line, line_discount, quantity)
            discount_applied += line_discount
        return results.BasketDiscount(discount)

    def clean(self):
        if self.instance.range:
            raise ValidationError(
                _("No range should be selected as the condition range will "
                  "be used instead."))


class MultibuyDiscountBenefit(BenefitImplementation):
    _description = _("Cheapest product from %(range)s is free")
    help_text = _("Discount is to give the cheapest product for free")
    verbose_name = _("Multibuy discount benefit")
    verbose_name_plural = _("Multibuy discount benefits")

    @property
    def name(self):
        return self._description % {
            'range': self.range.name.lower()}

    @property
    def description(self):
        return self._description % {
            'range': utils.range_anchor(self.range)}

    def apply(self, basket, condition, offer):
        line_tuples = self.get_applicable_lines(offer, basket)
        if not line_tuples:
            return results.ZERO_DISCOUNT

        # Cheapest line gives free product
        discount, line = line_tuples[0]
        apply_discount(line, discount, 1)

        affected_lines = [(line, discount, 1)]
        condition.consume_items(offer, basket, affected_lines)

        return results.BasketDiscount(discount)

    def clean(self):
        if not self.instance.range:
            raise ValidationError(
                _("Multibuy benefits require a product range"))
        if self.instance.value:
            raise ValidationError(
                _("Multibuy benefits don't require a value"))
        if self.instance.max_affected_items:
            raise ValidationError(
                _("Multibuy benefits don't require a 'max affected items' "
                  "attribute"))


# =================
# Shipping benefits
# =================


class ShippingBenefit(BenefitImplementation):

    def apply(self, basket, condition, offer):
        condition.consume_items(offer, basket, affected_lines=())
        return results.SHIPPING_DISCOUNT


class ShippingAbsoluteDiscountBenefit(ShippingBenefit):
    _description = _("%(amount)s off shipping cost")
    help_text = _("Discount is a fixed amount of the shipping cost")
    verbose_name = _("Shipping absolute discount benefit")
    verbose_name_plural = _("Shipping absolute discount benefits")

    @property
    def name(self):
        return self._description % {'amount': currency(self.value)}

    def shipping_discount(self, charge):
        return min(charge, self.value)

    def clean(self):
        if not self.instance.value:
            raise ValidationError(
                _("A discount value is required"))
        if self.instance.range:
            raise ValidationError(
                _("No range should be selected as this benefit does not "
                  "apply to products"))
        if self.instance.max_affected_items:
            raise ValidationError(
                _("Shipping discounts don't require a 'max affected items' "
                  "attribute"))


class ShippingFixedPriceBenefit(ShippingBenefit):
    _description = _("Get shipping for %(amount)s")
    help_text = _("Get shipping for a fixed price")
    verbose_name = _("Fixed price shipping benefit")
    verbose_name_plural = _("Fixed price shipping benefits")

    @property
    def name(self):
        return self._description % {'amount': currency(self.value)}

    def shipping_discount(self, charge):
        if charge < self.value:
            return D('0.00')
        return charge - self.value

    def clean(self):
        if self.instance.range:
            raise ValidationError(
                _("No range should be selected as this benefit does not "
                  "apply to products"))
        if self.instance.max_affected_items:
            raise ValidationError(
                _("Shipping discounts don't require a 'max affected items' "
                  "attribute"))


class ShippingPercentageDiscountBenefit(ShippingBenefit):
    _description = _("%(value)s%% off of shipping cost")
    help_text = _("Discount is a percentage off of the shipping cost")
    verbose_name = _("Shipping percentage discount benefit")
    verbose_name_plural = _("Shipping percentage discount benefits")

    @property
    def name(self):
        return self._description % {'value': self.value}

    def shipping_discount(self, charge):
        discount = charge * self.value / D('100.0')
        return discount.quantize(D('0.01'))

    def clean(self):
        if self.instance.value > 100:
            raise ValidationError(
                _("Percentage discount cannot be greater than 100"))
        if self.instance.range:
            raise ValidationError(
                _("No range should be selected as this benefit does not "
                  "apply to products"))
        if self.instance.max_affected_items:
            raise ValidationError(
                _("Shipping discounts don't require a 'max affected items' "
                  "attribute"))
