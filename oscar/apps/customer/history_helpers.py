import json

from django.dispatch import receiver
from django.conf import settings

from oscar.core.loading import import_module
product_viewed = import_module('catalogue.signals', ['product_viewed']).product_viewed

MAX_PRODUCTS = settings.OSCAR_RECENTLY_VIEWED_PRODUCTS

# Helpers

def get_recently_viewed_product_ids(request):
    u"""
    Returns the list of ids of the last products browsed by the user

    Limited to the max number defined in settings.py
    under OSCAR_RECENTLY_VIEWED_PRODUCTS.
    """
    try:
        product_ids = json.loads(request.COOKIES.get('oscar_recently_viewed_products'))
    except (ValueError, TypeError):
        return []
    if not isinstance(product_ids, list):
        return []
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
                        json.dumps(product_ids),
                        httponly=True)

# Receivers

@receiver(product_viewed)
def receive_product_view(sender, product, user, request, response, **kwargs):
    """
    Receiver to handle viewing single product pages

    Requires the request and response objects due to dependence on cookies
    """
    return _update_recently_viewed_products(product, request, response)
