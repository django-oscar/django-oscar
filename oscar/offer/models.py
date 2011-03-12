from oscar.offer.abstract_models import (AbstractConditionalOffer, AbstractCondition,
                                         AbstractBenefit, AbstractRange)


class ConditionalOffer(AbstractConditionalOffer):
    pass


class Condition(AbstractCondition):
    pass


class CountCondition(Condition):

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

    class Meta:
        proxy = True

    def is_satisfied(self, basket):
        value_of_matches = 0
        for line in basket.lines.all():
            if self.range.contains_product(line.product) and line.product.has_stockrecord:
                value_of_matches += line.product.stockrecord.price_incl_tax * line.quantity
            if value_of_matches >= self.value:
                return True
        return False


class Benefit(AbstractBenefit):
    pass


class Range(AbstractRange):
    pass