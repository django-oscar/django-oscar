from decimal import Decimal, ROUND_DOWN, ROUND_UP
import math
from django.utils.translation import ungettext, ugettext as _
from oscar.apps.offer.abstract_models import AbstractConditionalOffer, AbstractCondition, AbstractBenefit, AbstractRange


class ConditionalOffer(AbstractConditionalOffer):
    pass


class Condition(AbstractCondition):
    pass


class Benefit(AbstractBenefit):
    pass

class Range(AbstractRange):
    pass

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

    def consume_items(self, basket, lines=None, value=None):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.
        """
        lines = lines or basket.all_lines()
        consumed_products = []
        value = self.value if value is None else value
        for line in lines:

            if self.can_apply_condition(line.product):
                quantity_to_consume = min(line.quantity_without_discount,
                                          value - len(consumed_products))
                line.consume(quantity_to_consume)
                consumed_products.extend((line.product,)*int(quantity_to_consume))
            if len(consumed_products) == value:
                break
        return consumed_products


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

    def consume_items(self, basket, lines=None, value=None):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.
        """
        lines = lines or basket.all_lines()
        consumed_products = []
        value = self.value if value is None else value
        for line in basket.all_lines():
            product = line.product
            if (line.is_available_for_discount and self.can_apply_condition(product)
                and product not in consumed_products):
                line.consume(1)
                consumed_products.append(line.product)
            if len(consumed_products) >= value:
                break
        return consumed_products

    def get_value_of_satisfying_items(self, basket):
        covered_ids = []
        value = Decimal('0.00')
        for line in basket.all_lines():
            if (self.can_apply_condition(line.product) and line.product.id not in covered_ids):
                covered_ids.append(line.product.id)
                value += line.unit_price_incl_tax
            if len(covered_ids) >= self.value:
                return value
        return value


class ValueCondition(Condition):
    """
    An offer condition dependent on the VALUE of matching items from the basket.
    """
    price_field = 'price_incl_tax'

    class Meta:
        proxy = True
        verbose_name = _("Value Condition")
        verbose_name_plural = _("Value Conditions")


    def is_satisfied(self, basket):
        """Determines whether a given basket meets this condition"""
        value_of_matches = Decimal('0.00')
        for line in basket.all_lines():
            product = line.product
            if (self.can_apply_condition(product) and product.has_stockrecord
                and line.quantity_without_discount > 0):
                price = getattr(product.stockrecord, self.price_field)
                value_of_matches += price * int(line.quantity_without_discount)
            if value_of_matches >= self.value:
                return True
        return False

    def _get_value_of_matches(self, basket):
        if hasattr(self, '_value_of_matches'):
            return getattr(self, '_value_of_matches')
        value_of_matches = Decimal('0.00')
        for line in basket.all_lines():
            product = line.product
            if (self.can_apply_condition(product) and product.has_stockrecord
                and line.quantity_without_discount > 0):
                price = getattr(product.stockrecord, self.price_field)
                value_of_matches += price * int(line.quantity_without_discount)
        self._value_of_matches = value_of_matches
        return value_of_matches

    def is_partially_satisfied(self, basket):
        value_of_matches = self._get_value_of_matches(basket)
        return Decimal('0.00') < value_of_matches < self.value

    def get_upsell_message(self, basket):
        value_of_matches = self._get_value_of_matches(basket)
        return _('Spend %(value)s more from %(range)s') % {'value': value_of_matches, 'range': self.range}

    def consume_items(self, basket, lines=None, value=None):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.

        We allow lines to be passed in as sometimes we want them sorted
        in a specific order.
        """
        value_of_matches = Decimal('0.00')
        lines = lines or basket.all_lines()
        consumed_products = []
        value = self.value if value is None else value
        for line in basket.all_lines():
            product = line.product
            if (self.can_apply_condition(product) and product.has_stockrecord):
                price = getattr(product.stockrecord, self.price_field)
                if not price:
                    continue
                quantity_to_consume = min(line.quantity_without_discount,
                                          int(((value - value_of_matches)/price).quantize(Decimal(1),
                                                                                              ROUND_UP)))
                value_of_matches += price * quantity_to_consume
                line.consume(quantity_to_consume)
                consumed_products.extend((line.product,)*int(quantity_to_consume))
            if value_of_matches >= value:
                break
        return consumed_products

# ========
# Benefits
# ========

class PercentageDiscountBenefit(Benefit):
    """
    An offer benefit that gives a percentage discount
    """

    class Meta:
        proxy = True
        verbose_name = _("Percentage Discount Benefit")
        verbose_name_plural = _("Percentage Discount Benefits")

    def apply(self, basket, condition=None):
        discount = Decimal('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()

        for line in basket.all_lines():
            if affected_items >= max_affected_items:
                break
            product = line.product
            if (self.range.contains_product(product) and product.has_stockrecord
                and self.can_apply_benefit(product)):
                price = getattr(product.stockrecord, self.price_field)
                quantity = min(line.quantity_without_discount,
                               max_affected_items - affected_items)
                line_discount = self.round(self.value/100 * price * int(quantity))
                line.discount(line_discount, quantity)
                affected_items += quantity
                discount += line_discount

        if discount > 0 and condition:
            condition.consume_items(basket)
        return discount


class AbsoluteDiscountBenefit(Benefit):
    """
    An offer benefit that gives an absolute discount
    """

    class Meta:
        proxy = True
        verbose_name = _("Absolute Discount Benefit")
        verbose_name_plural = _("Absolute Discount Benefits")

    def apply(self, basket, condition=None):
        discount = Decimal('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()

        for line in basket.all_lines():
            if affected_items >= max_affected_items:
                break
            product = line.product
            if (self.range.contains_product(product) and product.has_stockrecord
                and self.can_apply_benefit(product)):
                price = getattr(product.stockrecord, self.price_field)
                if not price:
                    # Avoid zero price products
                    continue
                remaining_discount = self.value - discount
                quantity_affected = int(min(line.quantity_without_discount,
                                        max_affected_items - affected_items,
                                        math.ceil(remaining_discount / price)))

                # Update line with discounts
                line_discount = self.round(min(remaining_discount, quantity_affected * price))
                if condition:
                    # Pass zero as quantity to avoid double consumption
                    line.discount(line_discount, 0)
                else:
                    line.discount(line_discount, quantity_affected)

                # Update loop vars
                affected_items += quantity_affected
                remaining_discount -= line_discount
                discount += line_discount

        if discount > 0 and condition:
            condition.consume_items(basket)

        return discount


class FixedPriceBenefit(Benefit):
    """
    An offer benefit that gives the items in the condition for a
    fixed price.  This is useful for "bundle" offers.

    Note that we ignore the benefit range here and only give a fixed price
    for the products in the condition range.

    The condition should be a count condition
    """
    class Meta:
        proxy = True
        verbose_name = _("Fixed Price Benefit")
        verbose_name_plural = _("Fixed Price Benefits")

    def apply(self, basket, condition=None):
        num_covered = 0
        num_permitted = int(condition.value)
        covered_lines = []
        product_total = Decimal('0.00')
        for line in basket.all_lines():
            product = line.product
            if (condition.range.contains_product(product) and line.quantity_without_discount > 0
                and self.can_apply_benefit(product)):
                # Line is available - determine quantity to consume and
                # record the total of the consumed products
                if isinstance(condition, CoverageCondition):
                    quantity = 1
                else:
                    quantity = min(line.quantity_without_discount, num_permitted - num_covered)
                num_covered += quantity
                product_total += quantity*line.unit_price_incl_tax
                covered_lines.append((line, quantity))
            if num_covered >= num_permitted:
                break
        discount = max(product_total - self.value, Decimal('0.00'))

        if not discount:
            return discount

        # Apply discount weighted by original value of line
        discount_applied = Decimal('0.00')
        last_line = covered_lines[-1][0]
        for line, quantity in covered_lines:
            if line == last_line:
                # If last line, we just take the difference to ensure that
                # a rounding doesn't lead to an off-by-one error
                line_discount = discount - discount_applied
            else:
                line_discount = self.round(discount * (line.unit_price_incl_tax * quantity) / product_total)
            line.discount(line_discount, quantity)
            discount_applied += line_discount
        return discount


class MultibuyDiscountBenefit(Benefit):

    class Meta:
        proxy = True
        verbose_name = _("Multibuy Discount Benefit")
        verbose_name_plural = _("Multibuy Discount Benefits")

    def apply(self, basket, condition=None):
        benefit_lines = [line for line in basket.all_lines() if (self.range.contains_product(line.product) and
                                                                 line.quantity_without_discount > 0 and
                                                                 line.product.has_stockrecord and
                                                                 self.can_apply_benefit(line.product))]
        if not benefit_lines:
            return self.round(Decimal('0.00'))

        # Determine cheapest line to give for free
        line_price_getter = lambda line: getattr(line.product.stockrecord,
                                                 self.price_field)
        free_line = min(benefit_lines, key=line_price_getter)
        discount = line_price_getter(free_line)

        if condition:
            compare = lambda l1, l2: cmp(line_price_getter(l2),
                                         line_price_getter(l1))
            lines_with_price = [line for line in basket.all_lines() if line.product.has_stockrecord]
            sorted_lines = sorted(lines_with_price, compare)
            free_line.discount(discount, 1)
            if condition.range.contains_product(free_line.product):
                condition.consume_items(basket, lines=sorted_lines,
                                        value=condition.value-1)
            else:
                condition.consume_items(basket, lines=sorted_lines)
        else:
            free_line.discount(discount, 0)
        return self.round(discount)
