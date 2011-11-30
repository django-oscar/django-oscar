import json

from django.dispatch import receiver
from django.conf import settings

from oscar.core.loading import import_module
import_module('catalogue.signals', ['product_viewed'], locals())

MAX_PRODUCTS = settings.OSCAR_RECENTLY_VIEWED_PRODUCTS

# Helpers

def get_recently_viewed_product_ids(request):
    u"""
    Returns the list of ids of the last products browsed by the user
    
    Limited to the max number defined in settings.py
    under OSCAR_RECENTLY_VIEWED_PRODUCTS.
    """
    product_ids = [];
    if (request.COOKIES.has_key('oscar_recently_viewed_products')):
        try:
            product_ids = _get_list_from_json_string(request.COOKIES['oscar_recently_viewed_products'])
        except ValueError:
            # This can occur if something messes up the cookie
            pass
    return product_ids

def _update_recently_viewed_products(product, request, response):
    """
    Updates the cookies that store the recently viewed products
    removing possible duplicates.
    """
    product_ids = get_recently_viewed_product_ids(request)
    if product.id in product_ids:
        product_ids.remove(product.id)
    product_ids.append(product.id)
    if (len(product_ids) > MAX_PRODUCTS):
        product_ids = product_ids[len(product_ids)-MAX_PRODUCTS:]
    response.set_cookie('oscar_recently_viewed_products', 
                        _get_json_string_from_list(product_ids),
                        httponly=True)

def _get_list_from_json_string(cookie_value):
    u""" Simple function to convert lists to json """
    return json.loads(cookie_value)

def _get_json_string_from_list(list):
    """ Simple function to convert json to a python list """
    return json.dumps(list)


# Receivers

@receiver(product_viewed)
def receive_product_view(sender, product, user, request, response, **kwargs):
    """
    Receiver to handle viewing single product pages
    
    Requires the request and response objects due to dependence on cookies
    """
    return _update_recently_viewed_products(product, request, response)
