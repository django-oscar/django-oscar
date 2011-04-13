from django.dispatch import receiver
from django.conf import settings

from oscar.services import import_module

import json

product_signals = import_module('product.signals', ['product_viewed'])
max_products = settings.OSCAR_RECENTLY_VIEWED_PRODUCTS

# Helpers

def get_recently_viewed_product_ids(request):
    u"""
    The list of ids of the last products browsed by the user
    
    Limited to the max number defined in settings.py
    under OSCAR_RECENTLY_VIEWED_PRODUCTS.
    """
    product_ids = [];
    if (request.COOKIES.has_key('oscar_recently_viewed_products')):
        try:
            product_ids = _get_list_from_json_string(request.COOKIES['oscar_recently_viewed_products'])
        except ValueError:
            # This can occure if something messes up the cookie
            pass
    return product_ids

def _update_recently_viewed_products(product, request, response):
    u"""
    Updates the cookies that store the recently viewed products
    removing possible duplicates.
    """
    product_ids = get_recently_viewed_product_ids(request)
    if product.id in product_ids:
        product_ids.remove(product.id)
    product_ids.append(product.id)
    if (len(product_ids) > max_products):
        assert False
        del product_ids[max_products:]
    response.set_cookie('oscar_recently_viewed_products', _get_json_string_from_list(product_ids))
    return

def _get_list_from_json_string(cookie_value):
    u""" Simple function to convert lists to json """
    return json.loads(cookie_value)

def _get_json_string_from_list(list):
    u""" Simple function to convert json to a python list """
    return json.dumps(list)


# Receivers

@receiver(product_signals.product_viewed)
def receive_product_view(sender, product, user, request, response, **kwargs):
    u"""
    Receiver to handle viewing single product pages
    
    Requires the request and response objects due to dependence on cookies
    """
    return _update_recently_viewed_products(product, request, response)
