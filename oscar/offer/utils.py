from decimal import Decimal

from oscar.services import import_module
offer_models = import_module('offer.models', ['ConditionalOffer'])

class Applicator(object):
    
    def apply(self, basket):
        u"""
        Applies all relevant offers to the given basket.
        """
        offers = self._get_offers(basket)
        discounts = {}
        for offer in offers:
            # For each offer, we keep trying to apply it until the
            # discount is 0
            while True:
                discount = offer.apply_benefit(basket)
                if discount > 0:
                    if offer.id not in discounts:
                        discounts[offer.id] = {'name': offer.name,
                                               'freq': 0,
                                               'discount': Decimal('0.00')} 
                    discounts[offer.id]['discount'] += discount
                    discounts[offer.id]['freq'] += 1
                else:
                    break
                
        # Store this list of discounts with the basket so it can be 
        # rendered in templates
        basket.set_discounts(list(discounts.values()))
    
    def _get_offers(self, basket):
        u"""
        Returns all offers to apply to the basket.
        """
        return offer_models.ConditionalOffer.active.all()
        