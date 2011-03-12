from decimal import Decimal
import math

from oscar.offer.abstract_models import (AbstractConditionalOffer, AbstractCondition,
                                         AbstractBenefit, AbstractRange)


class ConditionalOffer(AbstractConditionalOffer):
    pass


class Condition(AbstractCondition):
    pass


class CountCondition(Condition):
    u"""
    An offer condition dependent on the NUMBER of matching items from the basket.
    """

    class Meta:
        proxy = True

    def is_satisfied(self, basket):
        u"""Determines whether a given basket meets this condition"""
        num_matches = 0
        for line in basket.lines.all():
            if self.range.contains_product(line.product):
                num_matches += line.quantity
            if num_matches >= self.value:
                return True
        return False
        
        
class ValueCondition(Condition):
    u"""
    An offer condition dependent on the VALUE of matching items from the basket.
    """
    price_field = 'price_incl_tax'

    class Meta:
        proxy = True

    def is_satisfied(self, basket):
        u"""Determines whether a given basket meets this condition"""
        value_of_matches = Decimal('0.00')
        for line in basket.lines.all():
            if self.range.contains_product(line.product) and line.product.has_stockrecord:
                price = getattr(line.product.stockrecord, self.price_field)
                value_of_matches += price * line.quantity
            if value_of_matches >= self.value:
                return True
        return False


class Benefit(AbstractBenefit):
    price_field = 'price_incl_tax'


class PercentageDiscountBenefit(Benefit):
    u"""
    An offer benefit that gives a percentage discount
    """

    class Meta:
        proxy = True

    def apply(self, basket):
        discount = Decimal('0.00')
        affected_items = 0
        max_affected_items = self.max_affected_items
        if not self.max_affected_items:
            max_affected_items = 10000
        
        for line in basket.lines.all():
            if affected_items >= max_affected_items:
                break
            if self.range.contains_product(line.product) and line.product.has_stockrecord:
                 price = getattr(line.product.stockrecord, self.price_field)
                 quantity = min(line.quantity, max_affected_items - affected_items)
                 discount += self.value/100 * price * quantity
                 affected_items += quantity
        return discount


class AbsoluteDiscountBenefit(Benefit):
    u"""
    An offer benefit that gives an absolute discount
    """

    class Meta:
        proxy = True

    def apply(self, basket):
        discount = Decimal('0.00')
        affected_items = 0
        max_affected_items = self.max_affected_items
        if not self.max_affected_items:
            max_affected_items = 10000
        
        for line in basket.lines.all():
            if affected_items >= max_affected_items:
                break
            if self.range.contains_product(line.product) and line.product.has_stockrecord:
                price = getattr(line.product.stockrecord, self.price_field)
                remaining_discount = self.value - discount
                quantity = min(line.quantity, math.floor(remaining_discount / price), max_affected_items - affected_items)
                discount += price * Decimal(str(quantity))
                affected_items += quantity
                 
        return discount


class Range(AbstractRange):
    pass