import zlib

from django.conf import settings

from oscar.services import import_module
from oscar.basket.models import SAVED

basket_models = import_module('basket.models', ['Basket', 'Line'])

COOKIE_KEY_USER_BASKET = 'oscar_basket'
COOKIE_KEY_SAVED_BASKET = 'oscar_saved_basket'
COOKIE_LIFETIME = 7*24*60*60

def get_or_create_basket(request, response):
    """
    Loads or creates a basket for the current user
    """
    anon_basket = _get_anon_user_basket(request)
    if request.user.is_authenticated():
        basket, created = basket_models.Basket.open.get_or_create(owner=request.user)
        if anon_basket:
            # If signed in user also has a cookie basket, we merge them and 
            # delete the cookies
            basket.merge(anon_basket)
            response.delete_cookie(COOKIE_KEY_USER_BASKET)
    elif not anon_basket:
        # No valid basket found for an unauthenticated user so we create a 
        # new one and store the id and hash in a cookie.
        basket = basket_models.Basket.objects.create()
        cookie = "%s_%s" % (basket.id, _get_basket_hash(basket.id))
        response.set_cookie(COOKIE_KEY_USER_BASKET, cookie, max_age=COOKIE_LIFETIME)
    else:
        basket = anon_basket
    return basket  

def get_or_create_saved_basket(request, response):
    """
    Loads or creates a "save-for-later" basket for the current user
    """
    anon_basket = _get_anon_saved_basket(request)
    if request.user.is_authenticated():
        basket, created = basket_models.Basket.saved.get_or_create(owner=request.user)
        if anon_basket:
            # If signed in user also has a cookie basket, we merge them and 
            # delete the cookies
            basket.merge(anon_basket)
            response.delete_cookie(COOKIE_KEY_SAVED_BASKET)
    elif not anon_basket:
        # No valid basket found for an unauthenticated user so we create a 
        # new one and store the id and hash in a cookie.
        basket = basket_models.Basket.objects.create(status=SAVED)
        cookie = "%s_%s" % (basket.id, _get_basket_hash(basket.id))
        response.set_cookie(COOKIE_KEY_SAVED_BASKET, cookie, max_age=COOKIE_LIFETIME)
    else:
        basket = anon_basket
    return basket 

def get_basket(request):
    """
    Returns the basket for the current user
    """
    b = None
    if request.user.is_authenticated():
        b = basket_models.Basket.open.get(owner=request.user)
    else:
        b = _get_anon_user_basket(request)
    return b    

def get_saved_basket(request):
    """
    Returns the saved basket for the current user
    """
    b = None
    if request.user.is_authenticated():
        try:
            b = basket_models.Basket.saved.get(owner=request.user)
        except basket_models.Basket.NotFound:
            pass
    else:
        b = _get_anon_saved_basket(request)
    return b  

def _get_anon_user_basket(request):
    """
    Looks for a basket that has its ID stored in the user's cookies
    """
    b = None
    # If user is anonymous, their basket ID (if they have one) will be
    # stored in a cookie together with a hash which verifies it and prevents
    # it from being spoofed.
    if request.COOKIES.has_key(COOKIE_KEY_USER_BASKET):
        basket_id, basket_hash = request.COOKIES[COOKIE_KEY_USER_BASKET].split("_")
        if basket_hash == _get_basket_hash(basket_id):
            try:
                b = basket_models.Basket.open.get(pk=basket_id)
            except basket_models.Basket.DoesNotExist, e:
                b = None
    return b    

def _get_anon_saved_basket(request):
    """
    Looks for a basket that has its ID stored in the user's cookies
    """
    b = None
    # If user is anonymous, their basket ID (if they have one) will be
    # stored in a cookie together with a hash which verifies it and prevents
    # it from being spoofed.
    if COOKIE_KEY_SAVED_BASKET in request.COOKIES:
        basket_id, basket_hash = request.COOKIES[COOKIE_KEY_SAVED_BASKET].split("_")
        if basket_hash == _get_basket_hash(basket_id):
            try:
                b = basket_models.Basket.saved.get(pk=basket_id)
            except basket_models.Basket.DoesNotExist, e:
                b = None
    return b    


def _get_basket_hash(id):
    """
    Create a hash of the basket ID using the SECRET_KEY
    variable defined in settings.py as a salt.
    """
    return str(zlib.crc32(str(id)+settings.SECRET_KEY))