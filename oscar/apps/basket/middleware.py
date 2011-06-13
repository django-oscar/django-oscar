import zlib

from django.conf import settings
from django.core.exceptions import SuspiciousOperation

from django.db.models import get_model

from oscar.core.loading import import_module
import_module('offer.utils', ['Applicator'], locals())

basket_model = get_model('basket', 'basket')

class BasketMiddleware(object):
    
    cookies_to_delete = []
    
    def process_request(self, request):
        
        manager = basket_model.open
        cookie_basket = self.get_cookie_basket(settings.OSCAR_BASKET_COOKIE_OPEN, 
                                               request, manager)
        if request.user.is_authenticated():
            # Signed-in user: if they have a cookie basket too, it means
            # that they have just signed in and we need to merge their cookie
            # basket into their user basket, then delete the cookie
            basket, _ = manager.get_or_create(owner=request.user)
            if cookie_basket:
                basket.merge(cookie_basket)
                self.cookies_to_delete.append(settings.OSCAR_BASKET_COOKIE_OPEN)
        elif cookie_basket:
            # Anonymous user with a basket tied to the cookie
            basket = cookie_basket
        else:
            # Anonymous user with no basket - we don't save the basket until
            # we need to.
            basket = basket_model()
            
        # Assign basket object to request
        self.apply_offers_to_basket(request, basket)   
        request.basket = basket
        
    def process_response(self, request, response):
        
        # Delete any surplus cookies
        for cookie_key in self.cookies_to_delete:
            response.delete_cookie(cookie_key)
            
        # If a basket has had products added to it, but the user is anonymous
        # then we need to assign it to a cookie
        if hasattr(request, 'basket') and request.basket.id > 0 and not request.user.is_authenticated():
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
            basket_id, basket_hash = request.COOKIES[cookie_key].split("_")
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
        return str(zlib.crc32(str(id)+settings.SECRET_KEY))
