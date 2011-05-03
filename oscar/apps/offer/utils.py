from decimal import Decimal
from itertools import chain

from oscar.core.loading import import_module
import_module('offer.models', ['ConditionalOffer'], locals())


class Applicator(object):
    u"""
    For applying offers to a basket.
    """
    
    def apply(self, request, basket):
        u"""
        Applies all relevant offers to the given basket.  The user is passed 
        too as sometimes the available offers are dependent on the user.
        """
        offers = self.get_offers(request, basket) 
        discounts = {}
        for offer in offers:
            # For each offer, we keep trying to apply it until the
            # discount is 0
            while True:
                discount = offer.apply_benefit(basket)
                if discount > 0:
                    if offer.id not in discounts:
                        discounts[offer.id] = {'name': offer.name,
                                               'offer': offer,
                                               'voucher': offer.get_voucher(),
                                               'freq': 0,
                                               'discount': Decimal('0.00')} 
                    discounts[offer.id]['discount'] += discount
                    discounts[offer.id]['freq'] += 1
                else:
                    break
                
        # Store this list of discounts with the basket so it can be 
        # rendered in templates
        basket.set_discounts(list(discounts.values()))
    
    def get_offers(self, request, basket):
        u"""
        Returns all offers to apply to the basket.
        
        This method should be subclassed and extended to provide more sophisticated
        behaviour.  For instance, you could load extra offers based on the session or
        the user type.
        """
        site_offers = self.get_site_offers()
        basket_offers = self.get_basket_offers(basket, request.user)
        user_offers = self.get_user_offers(request.user)
        session_offers = self.get_session_offers(request)
        
        return list(chain(site_offers, basket_offers, user_offers, session_offers))
        
    def get_site_offers(self):
        u"""
        Returns site offers that are available to all users
        """
        return ConditionalOffer.active.all()
    
    def get_basket_offers(self, basket, user):
        u"""
        Returns basket-linked offers such as those associated with a voucher code"""
        offers = []
        for voucher in basket.vouchers.all():
            if voucher.is_active() and voucher.is_available_to_user(user):
                basket_offers = voucher.offers.all()
                for offer in basket_offers:
                    offer.set_voucher(voucher)
                offers = list(chain(offers, basket_offers))
        return offers
    
    def get_user_offers(self, user):
        u"""
        Returns offers linked to this particular user.  
        
        Eg: student users might get 25% off
        """
        return []
    
    def get_session_offers(self, request):
        u"""
        Returns temporary offers linked to the current session.
        
        Eg: visitors coming from an affiliate site get a 10% discount
        """
        return []
        