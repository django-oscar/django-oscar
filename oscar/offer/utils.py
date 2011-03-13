from decimal import Decimal

from oscar.services import import_module
offer_models = import_module('offer.models', ['ConditionalOffer'])

class Applicator(object):
    
    def apply(self, basket):
        offers = self._get_offers(basket)
        discounts = {}
        for offer in offers:
            if offer.is_condition_satisfied(basket):
                discount = offer.apply_benefit(basket)
                if discount > 0:
                    if offer.id not in discounts:
                        discounts[offer.id] = {'name': offer.name,
                                               'freq': 0,
                                               'discount': Decimal('0.00')} 
                    discounts[offer.id]['discount'] += discount
                    discounts[offer.id]['freq'] += 1
        basket.set_discounts(list(discounts.values()))
    
    def _get_offers(self, basket):
        return offer_models.ConditionalOffer.active.all()