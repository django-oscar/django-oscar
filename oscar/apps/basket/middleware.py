import zlib

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.db.models import get_model

from oscar.core.loading import import_module
import_module('offer.utils', ['Applicator'], locals())
basket_model = get_model('basket', 'basket')


class BasketMiddleware(object):
    
    def process_request(self, request):
        self.cookies_to_delete = []
        basket = self.get_basket(request)
        self.apply_offers_to_basket(request, basket)   
        request.basket = basket
    
    def get_basket(self, request):  
        manager = basket_model.open
        cookie_basket = self.get_cookie_basket(settings.OSCAR_BASKET_COOKIE_OPEN, 
                                               request, manager)
        
        if request.user.is_authenticated():
            # Signed-in user: if they have a cookie basket too, it means
            # that they have just signed in and we need to merge their cookie
            # basket into their user basket, then delete the cookie
            try:
                basket, _ = manager.get_or_create(owner=request.user)
            except basket_model.MultipleObjectsReturned:
                # Not sure quite how we end up here with multiple baskets
                # We merge any  them and create a fresh one
                old_baskets = list(manager.filter(owner=request.user))
                basket = old_baskets[0]
                for other_basket in old_baskets[1:]:
                    self.merge_baskets(basket, other_basket)
                
            if cookie_basket:
                self.merge_baskets(basket, cookie_basket)
                self.cookies_to_delete.append(settings.OSCAR_BASKET_COOKIE_OPEN)
        elif cookie_basket:
            # Anonymous user with a basket tied to the cookie
            basket = cookie_basket
        else:
            # Anonymous user with no basket - we don't save the basket until
            # we need to.
            basket = basket_model() 
        return basket 
            
    def merge_baskets(self, master, slave):
        """
        Merge one basket into another.
        
        This is its own method to allow it to be overridden
        """
        master.merge(slave)    
        
    def process_response(self, request, response):
        
        # Delete any surplus cookies
        if hasattr(self, 'cookies_to_delete'):
            for cookie_key in self.cookies_to_delete:
                response.delete_cookie(cookie_key)
            
        # If a basket has had products added to it, but the user is anonymous
        # then we need to assign it to a cookie
        if hasattr(request, 'basket') and request.basket.id > 0 \
            and not request.user.is_authenticated() \
            and settings.OSCAR_BASKET_COOKIE_OPEN not in request.COOKIES:
            cookie = "%s_%s" % (request.basket.id, self.get_basket_hash(request.basket.id))
            response.set_cookie(settings.OSCAR_BASKET_COOKIE_OPEN, 
                                cookie, 
                                max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME, 
                                httponly=True)
        return response
    
    def process_template_response(self, request, response):
        if response.context_data is None:
            response.context_data = {}
        response.context_data['basket'] = request.basket
        return response
    
    def get_cookie_basket(self, cookie_key, request, manager):
        """
        Looks for a basket which is referenced by a cookie.
        
        If a cookie key is found with no matching basket, then we add
        it to the list to be deleted.
        """
        basket = None
        if cookie_key in request.COOKIES:
            parts = request.COOKIES[cookie_key].split("_")
            if len(parts) != 2:
                return basket
            basket_id, basket_hash = parts
            if basket_hash == self.get_basket_hash(basket_id):
                try:
                    basket = basket_model.objects.get(pk=basket_id, owner=None)
                except basket_model.DoesNotExist:
                    self.cookies_to_delete.append(cookie_key)
            else:
                self.cookies_to_delete.append(cookie_key)
        return basket    
    
    def apply_offers_to_basket(self, request, basket):
        if not basket.is_empty:
            Applicator().apply(request, basket)
    
    def get_basket_hash(self, basket_id):
        return str(zlib.crc32(str(basket_id)+settings.SECRET_KEY))
