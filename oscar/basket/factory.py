import zlib

from django.conf import settings

from oscar.services import import_module
basket_models = import_module('basket.models', ['Basket', 'Line'])

# Cookie keys
COOKIE_KEY_OPEN_BASKET = 'oscar_open_basket'
COOKIE_KEY_SAVED_BASKET = 'oscar_saved_basket'

try:
    # The lifetime for the basket cookie can be set in settings.py
    COOKIE_LIFETIME = settings.OSCAR_BASKET_COOKIE_LIFETIME
except AttributeError: 
    COOKIE_LIFETIME = 7*24*60*60


class BasketFactory(object):
    u"""Factory object for loading baskets."""

    def get_or_create_open_basket(self, request, response):
        u"""Loads or creates a normal OPEN basket for the current user (anonymous
        or not).
        """
        return self._get_or_create_cookie_basket(request, response, 
                                                 COOKIE_KEY_OPEN_BASKET, basket_models.Basket.open)
    
    def get_or_create_saved_basket(self, request, response):
        u"""Loads or creates a "save-for-later" basket for the current user"""
        return self._get_or_create_cookie_basket(request, response, 
                                                 COOKIE_KEY_SAVED_BASKET, basket_models.Basket.saved)
    
    def get_open_basket(self, request):
        u"""Returns the basket for the current user"""
        return self._get_basket(request, COOKIE_KEY_OPEN_BASKET, basket_models.Basket.open)
    
    def get_saved_basket(self, request):
        u"""Returns the saved basket for the current user"""
        return self._get_basket(request, COOKIE_KEY_SAVED_BASKET, basket_models.Basket.saved)
    
    # Utility methods
    
    def _get_or_create_cookie_basket(self, request, response, cookie_key, manager):
        u"""Loads or creates a basket for the current user"""
        anon_basket = self._get_cookie_basket(request, cookie_key, manager)
        if request.user.is_authenticated():
            basket, created = manager.get_or_create(owner=request.user)
            if anon_basket:
                # If signed in user also has a cookie basket, we merge them and 
                # delete the cookies
                basket.merge(anon_basket)
                response.delete_cookie(cookie_key)
        elif not anon_basket:
            # No valid basket found for an unauthenticated user so we create a 
            # new one and store the id and hash in a cookie.
            basket = manager.create()
            cookie = "%s_%s" % (basket.id, self._get_basket_hash(basket.id))
            response.set_cookie(cookie_key, cookie, max_age=COOKIE_LIFETIME, httponly=True)
        else:
            # Only the cookie basket found - return it
            basket = anon_basket
        return basket 
    
    def _get_basket(self, request, cookie_key, manager):
        u"""Returns a basket object given a cookie key and manager."""
        b = None
        if request.user.is_authenticated():
            try:
                b = manager.get(owner=request.user)
            except basket_models.Basket.DoesNotExist, e:
                pass
        else:
            b = self._get_cookie_basket(request, cookie_key, manager)
        return b    
        
    def _get_cookie_basket(self, request, cookie_key, manager):
        u"""Returns a basket based on the cookie key given."""
        b = None
        # If user is anonymous, their basket ID (if they have one) will be
        # stored in a cookie together with a hash which verifies it and prevents
        # it from being spoofed.
        if cookie_key in request.COOKIES:
            basket_id, basket_hash = request.COOKIES[cookie_key].split("_")
            if basket_hash == self._get_basket_hash(basket_id):
                try:
                    b = manager.get(pk=basket_id, owner=None)
                except basket_models.Basket.DoesNotExist, e:
                    b = None
            else:
                response.delete_cookie(cookie_key)
        return b      
    
    def _get_basket_hash(self, id):
        u"""
        Create a hash of the basket ID using the SECRET_KEY
        variable defined in settings.py as a salt.
        """
        return str(zlib.crc32(str(id)+settings.SECRET_KEY))