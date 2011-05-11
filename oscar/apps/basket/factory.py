import zlib

from django.conf import settings
from django.core.exceptions import SuspiciousOperation

from oscar.core.loading import import_module
import_module('basket.models', ['Basket', 'Line'], locals())
import_module('offer.utils', ['Applicator'], locals())

# Basket settings
COOKIE_KEY_OPEN_BASKET = settings.OSCAR_BASKET_COOKIE_OPEN
COOKIE_KEY_SAVED_BASKET = settings.OSCAR_BASKET_COOKIE_SAVED
COOKIE_LIFETIME = settings.OSCAR_BASKET_COOKIE_LIFETIME


class BasketFactory(object):
    """
    Factory object for loading baskets.
    """

    def get_or_create_open_basket(self, request, response):
        """
        Loads or creates a normal OPEN basket for the current user (anonymous
        or not).
        """
        return self._get_or_create_basket(request, response, 
                                          cookie_key=COOKIE_KEY_OPEN_BASKET, 
                                          manager=Basket.open)
    
    def get_or_create_saved_basket(self, request, response):
        u"""Loads or creates a "save-for-later" basket for the current user"""
        return self._get_or_create_basket(request, response, 
                                          cookie_key=COOKIE_KEY_SAVED_BASKET, 
                                          manager=Basket.saved)
    
    def get_open_basket(self, request):
        u"""Returns the basket for the current user"""
        return self._get_basket(request, COOKIE_KEY_OPEN_BASKET, Basket.open)
    
    def get_saved_basket(self, request):
        u"""Returns the saved basket for the current user"""
        return self._get_basket(request, COOKIE_KEY_SAVED_BASKET, Basket.saved)
    
    # Utility methods
    
    def _get_or_create_basket(self, request, response, cookie_key, manager):
        u"""
        Loads or creates a basket for the current user.  Any offers are also
        applied to the basket before it is returned.
        """
        anon_basket = self._get_cookie_basket(request, cookie_key, manager)
        if request.user.is_authenticated():
            basket, _ = manager.get_or_create(owner=request.user)
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
        self._apply_offers_to_basket(request, basket)
        return basket 
    
    def _apply_offers_to_basket(self, request, basket):
        Applicator().apply(request, basket)
    
    def _get_basket(self, request, cookie_key, manager):
        u"""Returns a basket object given a cookie key and manager."""
        if request.user.is_authenticated():
            try:
                basket = manager.get(owner=request.user)
            except Basket.DoesNotExist:
                basket = None
        else:
            basket = self._get_cookie_basket(request, cookie_key, manager)
        if basket:
            self._apply_offers_to_basket(request, basket)
        return basket    
        
    def _get_cookie_basket(self, request, cookie_key, manager):
        """
        Returns a basket based on the cookie key given.
    
        If user is anonymous, their basket ID (if they have one) will be
        stored in a cookie together with a hash which verifies it and prevents
        it from being spoofed.
        """
        basket = None
        if cookie_key in request.COOKIES:
            basket_id, basket_hash = request.COOKIES[cookie_key].split("_")
            if basket_hash == self._get_basket_hash(basket_id):
                try:
                    basket = manager.get(pk=basket_id, owner=None)
                except Basket.DoesNotExist:
                    basket = None
            else:
                raise SuspiciousOperation("Basket hash does not validate")
        return basket      
    
    def _get_basket_hash(self, id):
        u"""
        Create a hash of the basket ID using the SECRET_KEY
        variable defined in settings.py as a salt.
        """
        return str(zlib.crc32(str(id)+settings.SECRET_KEY))