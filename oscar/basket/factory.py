import zlib

from django.conf import settings

from oscar.services import import_module

basket_models = import_module('basket.models', ['Basket', 'Line'])

COOKIE_KEY_ID = 'basket_id'
COOKIE_KEY_HASH = 'basket_hash'
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
            response.delete_cookie(COOKIE_KEY_ID)
            response.delete_cookie(COOKIE_KEY_HASH)
    elif not anon_basket:
        # No valid basket found so we create a new one and store the id
        # and hash in a cookie.
        basket = basket_models.Basket.objects.create()
        response.set_cookie(COOKIE_KEY_ID, b.pk, max_age=COOKIE_LIFETIME)
        response.set_cookie(COOKIE_KEY_HASH, _get_basket_hash(b.pk), max_age=COOKIE_LIFETIME)
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


def _get_anon_user_basket(request):
    """
    Looks for a basket that has its ID stored in the user's cookies
    """
    b = None
    # If user is anonymous, their basket ID (if they have one) will be
    # stored in a cookie together with a hash which verifies it and prevents
    # it from being spoofed.
    if request.COOKIES.has_key(COOKIE_KEY_ID) and request.COOKIES.has_key(COOKIE_KEY_HASH):
        basket_id = request.COOKIES[COOKIE_KEY_ID]
        basket_hash = request.COOKIES[COOKIE_KEY_HASH]
        if basket_hash == _get_basket_hash(basket_id):
            try:
                b = basket_models.Basket.open.get(pk=basket_id)
            except basket_models.Basket.DoesNotExist, e:
                b = None
    return b      


def _get_basket_hash(id):
    """
    Create a hash of the basket ID using the SECRET_KEY
    variable defined in settings.py as a salt.
    """
    return str(zlib.crc32(str(id)+settings.SECRET_KEY))