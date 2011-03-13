from decimal import Decimal
import math

from oscar.offer.abstract_models import (AbstractConditionalOffer, AbstractCondition,
                                         AbstractBenefit, AbstractRange)


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
        for line in basket.all_lines():
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
        for line in basket.all_lines():
            if self.range.contains_product(line.product) and line.product.has_stockrecord:
                price = getattr(line.product.stockrecord, self.price_field)
                value_of_matches += price * line.quantity
            if value_of_matches >= self.value:
                return True
        return False


class Benefit(AbstractBenefit):
    price_field = 'price_incl_tax'
    
    def _effective_max_affected_items(self):
        max_affected_items = self.max_affected_items
        if not self.max_affected_items:
            max_affected_items = 10000
        return max_affected_items


class PercentageDiscountBenefit(Benefit):
    u"""
    An offer benefit that gives a percentage discount
    """

    class Meta:
        proxy = True

    def apply(self, basket):
        discount = Decimal('0.00')
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()
        
        for line in basket.all_lines():
            if affected_items >= max_affected_items:
                break
            if self.range.contains_product(line.product) and line.product.has_stockrecord:
                price = getattr(line.product.stockrecord, self.price_field)
                quantity = min(line.quantity_without_discount, 
                               max_affected_items - affected_items)
                discount += self.value/100 * price * quantity
                affected_items += quantity
                line.discount(discount, quantity)
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
        max_affected_items = self._effective_max_affected_items()
        
        for line in basket.all_lines():
            if affected_items >= max_affected_items:
                break
            if self.range.contains_product(line.product) and line.product.has_stockrecord:
                price = getattr(line.product.stockrecord, self.price_field)
                remaining_discount = self.value - discount
                quantity = min(line.quantity_without_discount, 
                               math.floor(remaining_discount / price), 
                               max_affected_items - affected_items)
                discount += price * Decimal(str(quantity))
                affected_items += quantity
                line.discount(discount, quantity)
        return discount


class ConditionalOffer(AbstractConditionalOffer):
    
    def _proxy_condition(self):
        u"""
        Returns the appropriate proxy model for the condition
        """
        field_dict = self.condition.__dict__
        del field_dict['_state']
        if self.condition.type == self.condition.COUNT:
            return CountCondition(**field_dict)
        elif self.condition.type == self.condition.VALUE:
            return ValueCondition(**field_dict)
        return self.condition
    
    def _proxy_benefit(self):
        u"""
        Returns the appropriate proxy model for the condition
        """
        field_dict = self.benefit.__dict__
        del field_dict['_state']
        if self.benefit.type == self.benefit.PERCENTAGE:
            return PercentageDiscountBenefit(**field_dict)
        elif self.benefit.type == self.benefit.FIXED:
            return AbsoluteDiscountBenefit(**field_dict)
        return self.benefit
    

class Range(AbstractRange):
    pass