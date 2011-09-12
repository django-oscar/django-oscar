from decimal import Decimal
from itertools import chain

from oscar.core.loading import import_module
import_module('offer.models', ['ConditionalOffer'], locals())

# This needs hooking into the offer application system.
class Discount(object):
    
    def __init__(self, offer):
        self.offer = offer
        self.discount = Decimal('0.00')
        self.frequency = 0
        
    def discount(self, discount):
        self.discount += discount
        self.frequency += 1
        
    def is_voucher_discount(self):
        return bool(self.offer.get_voucher())

    def get_voucher(self):
        return self.offer.get_voucher()


class Applicator(object):
    """
    For applying offers to a basket.
    """
    
    def apply(self, request, basket):
        """
        Apply all relevant offers to the given basket.  The request and user is passed 
        too as sometimes the available offers are dependent on the user (eg session-based
        offers).
        """
        offers = self.get_offers(request, basket) 
        discounts = self.get_basket_discounts(basket, offers)
        # Store this list of discounts with the basket so it can be 
        # rendered in templates
        basket.set_discounts(list(discounts.values()))
        
    def get_basket_discounts(self, basket, offers):    
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
        return discounts
    
    def get_offers(self, request, basket):
        """
        Return all offers to apply to the basket.
        
        This method should be subclassed and extended to provide more sophisticated
        behaviour.  For instance, you could load extra offers based on the session or
        the user type.
        """
        site_offers = self.get_site_offers()
        basket_offers = self.get_basket_offers(basket, request.user)
        user_offers = self.get_user_offers(request.user)
        session_offers = self.get_session_offers(request)
        
        return list(chain(session_offers, basket_offers, user_offers, site_offers))
        
    def get_site_offers(self):
        u"""
        Return site offers that are available to all users
        """
        return ConditionalOffer.active.filter(offer_type=ConditionalOffer.SITE)
    
    def get_basket_offers(self, basket, user):
        """
        Return basket-linked offers such as those associated with a voucher code"""
        offers = []
        if not basket.id:
            return offers
        
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
        