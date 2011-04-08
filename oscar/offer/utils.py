from decimal import Decimal
from itertools import chain

from oscar.services import import_module
offer_models = import_module('offer.models', ['ConditionalOffer'])


class Applicator(object):
    u"""
    For applying offers to a basket.
    """
    
    def apply(self, request, basket):
        u"""
        Applies all relevant offers to the given basket.  The user is passed 
        too as sometimes the available offers are dependent on the user
        """
        offers = self._get_offers(request, basket)
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
    
    def _get_offers(self, request, basket):
        u"""
        Returns all offers to apply to the basket.
        
        This method should be subclassed and extended to provide more sophisticated
        behavoiur.  For instance, you could load extra offers based on the session or
        the user type.
        """
        return offer_models.ConditionalOffer.active.all()
        