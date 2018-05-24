from decimal import Decimal as D

from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_classes, get_model
from oscar.templatetags.currency_filters import currency

Benefit = get_model('offer', 'Benefit')
BasketDiscount, SHIPPING_DISCOUNT, ZERO_DISCOUNT = get_classes('offer.results', [
    'BasketDiscount', 'SHIPPING_DISCOUNT', 'ZERO_DISCOUNT'])
CoverageCondition, ValueCondition = get_classes('offer.conditions', ['CoverageCondition', 'ValueCondition'])
range_anchor = get_class('offer.utils', 'range_anchor')

__all__ = [
    'PercentageDiscountBenefit', 'AbsoluteDiscountBenefit', 'FixedPriceBenefit',
    'ShippingBenefit', 'MultibuyDiscountBenefit',
    'ShippingAbsoluteDiscountBenefit', 'ShippingFixedPriceBenefit',
    'ShippingPercentageDiscountBenefit',
]


def apply_discount(line, discount, quantity, offer=None):
    """
    Apply a given discount to the passed basket
    """
    line.discount(discount, quantity, incl_tax=False, offer=offer)


class PercentageDiscountBenefit(Benefit):
    """
    An offer benefit that gives a percentage discount
    """
    _description = _("%(value)s%% discount on %(range)s")

    @property
    def name(self):
        return self._description % {
            'value': self.value,
            'range': self.range.name}

    @property
    def description(self):
        return self._description % {
            'value': self.value,
            'range': range_anchor(self.range)}

    class Meta:
        app_label = 'offer'
        proxy = True
        verbose_name = _("Percentage discount benefit")
        verbose_name_plural = _("Percentage discount benefits")

    def apply(self, basket, condition, offer, discount_percent=None,
              max_total_discount=None):
        if discount_percent is None:
            discount_percent = self.value

        discount_amount_available = max_total_discount

        line_tuples = self.get_applicable_lines(offer, basket)
        discount_percent = min(discount_percent, D('100.0'))
        discount = D('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()
        affected_lines = []
        for price, line in line_tuples:
            if affected_items >= max_affected_items:
                break
            if discount_amount_available == 0:
                break

            quantity_affected = min(
                line.quantity_without_offer_discount(offer),
                max_affected_items - affected_items)
            line_discount = self.round(discount_percent / D('100.0') * price
                                       * int(quantity_affected))

            if discount_amount_available is not None:
                line_discount = min(line_discount, discount_amount_available)
                discount_amount_available -= line_discount

            apply_discount(line, line_discount, quantity_affected, offer)

            affected_lines.append((line, line_discount, quantity_affected))
            affected_items += quantity_affected
            discount += line_discount

        if discount > 0:
            condition.consume_items(offer, basket, affected_lines)
        return BasketDiscount(discount)


class AbsoluteDiscountBenefit(Benefit):
    """
    An offer benefit that gives an absolute discount
    """
    _description = _("%(value)s discount on %(range)s")

    @property
    def name(self):
        return self._description % {
            'value': currency(self.value),
            'range': self.range.name.lower()}

    @property
    def description(self):
        return self._description % {
            'value': currency(self.value),
            'range': range_anchor(self.range)}

    class Meta:
        app_label = 'offer'
        proxy = True
        verbose_name = _("Absolute discount benefit")
        verbose_name_plural = _("Absolute discount benefits")

    def apply(self, basket, condition, offer, discount_amount=None,
              max_total_discount=None):
        if discount_amount is None:
            discount_amount = self.value

        # Fetch basket lines that are in the range and available to be used in
        # an offer.
        line_tuples = self.get_applicable_lines(offer, basket)

        # Determine which lines can have the discount applied to them
        max_affected_items = self._effective_max_affected_items()
        num_affected_items = 0
        affected_items_total = D('0.00')
        lines_to_discount = []
        for price, line in line_tuples:
            if num_affected_items >= max_affected_items:
                break
            qty = min(
                line.quantity_without_offer_discount(offer),
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
            return ZERO_DISCOUNT

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
            apply_discount(line, line_discount, qty, offer)
            affected_lines.append((line, line_discount, qty))
            applied_discount += line_discount

        condition.consume_items(offer, basket, affected_lines)

        return BasketDiscount(discount)


class FixedPriceBenefit(Benefit):
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

    @property
    def name(self):
        return self._description % {
            'amount': currency(self.value)}

    class Meta:
        app_label = 'offer'
        proxy = True
        verbose_name = _("Fixed price benefit")
        verbose_name_plural = _("Fixed price benefits")

    def apply(self, basket, condition, offer):  # noqa (too complex (10))
        if isinstance(condition, ValueCondition):
            return ZERO_DISCOUNT

        # Fetch basket lines that are in the range and available to be used in
        # an offer.
        line_tuples = self.get_applicable_lines(offer, basket,
                                                range=condition.range)
        if not line_tuples:
            return ZERO_DISCOUNT

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
                    line.quantity_without_offer_discount(offer),
                    num_permitted - num_affected)
            num_affected += quantity_affected
            value_affected += quantity_affected * price
            covered_lines.append((price, line, quantity_affected))
            if num_affected >= num_permitted:
                break
        discount = max(value_affected - self.value, D('0.00'))
        if not discount:
            return ZERO_DISCOUNT

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
            apply_discount(line, line_discount, quantity, offer)
            discount_applied += line_discount
        return BasketDiscount(discount)


class MultibuyDiscountBenefit(Benefit):
    _description = _("Cheapest product from %(range)s is free")

    @property
    def name(self):
        return self._description % {
            'range': self.range.name.lower()}

    @property
    def description(self):
        return self._description % {
            'range': range_anchor(self.range)}

    class Meta:
        app_label = 'offer'
        proxy = True
        verbose_name = _("Multibuy discount benefit")
        verbose_name_plural = _("Multibuy discount benefits")

    def apply(self, basket, condition, offer):
        line_tuples = self.get_applicable_lines(offer, basket)
        if not line_tuples:
            return ZERO_DISCOUNT

        # Cheapest line gives free product
        discount, line = line_tuples[0]
        apply_discount(line, discount, 1, offer)

        affected_lines = [(line, discount, 1)]
        condition.consume_items(offer, basket, affected_lines)

        return BasketDiscount(discount)


# =================
# Shipping benefits
# =================


class ShippingBenefit(Benefit):

    def apply(self, basket, condition, offer):
        condition.consume_items(offer, basket, affected_lines=())
        return SHIPPING_DISCOUNT

    class Meta:
        app_label = 'offer'
        proxy = True


class ShippingAbsoluteDiscountBenefit(ShippingBenefit):
    _description = _("%(amount)s off shipping cost")

    @property
    def name(self):
        return self._description % {
            'amount': currency(self.value)}

    class Meta:
        app_label = 'offer'
        proxy = True
        verbose_name = _("Shipping absolute discount benefit")
        verbose_name_plural = _("Shipping absolute discount benefits")

    def shipping_discount(self, charge):
        return min(charge, self.value)


class ShippingFixedPriceBenefit(ShippingBenefit):
    _description = _("Get shipping for %(amount)s")

    @property
    def name(self):
        return self._description % {
            'amount': currency(self.value)}

    class Meta:
        app_label = 'offer'
        proxy = True
        verbose_name = _("Fixed price shipping benefit")
        verbose_name_plural = _("Fixed price shipping benefits")

    def shipping_discount(self, charge):
        if charge < self.value:
            return D('0.00')
        return charge - self.value


class ShippingPercentageDiscountBenefit(ShippingBenefit):
    _description = _("%(value)s%% off of shipping cost")

    @property
    def name(self):
        return self._description % {
            'value': self.value}

    class Meta:
        app_label = 'offer'
        proxy = True
        verbose_name = _("Shipping percentage discount benefit")
        verbose_name_plural = _("Shipping percentage discount benefits")

    def shipping_discount(self, charge):
        discount = charge * self.value / D('100.0')
        return discount.quantize(D('0.01'))
