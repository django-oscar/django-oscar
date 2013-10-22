import json

from django.dispatch import receiver
from django.conf import settings
from django.db.models import get_model

from oscar.core.loading import get_class

Product = get_model('catalogue', 'Product')
product_viewed = get_class('catalogue.signals', 'product_viewed')

COOKIE_NAME = 'oscar_history'
MAX_PRODUCTS = settings.OSCAR_RECENTLY_VIEWED_PRODUCTS


def get(request):
    """
    Return a list of recently viewed products
    """
    ids = extract(request)

    # Reordering as the ID order gets messed up in the query
    product_dict = Product.browsable.in_bulk(ids)
    ids.reverse()
    return [product_dict[id] for id in ids if id in product_dict]


def extract(request, response=None):
    """
    Extract the IDs of products in the history cookie
    """
    ids = []
    if COOKIE_NAME in request.COOKIES:
        try:
            ids = json.loads(request.COOKIES[COOKIE_NAME])
        except ValueError:
            # This can occur if something messes up the cookie
            if response:
                response.delete_cookie(COOKIE_NAME)
    return ids


def add(ids, new_id):
    """
    Add a new product ID to the list of product IDs
    """
    if new_id in ids:
        ids.remove(new_id)
    ids.append(new_id)
    if (len(ids) > MAX_PRODUCTS):
        ids = ids[len(ids) - MAX_PRODUCTS:]
    return ids


def update(product, request, response):
    """
    Updates the cookies that store the recently viewed products
    removing possible duplicates.
    """
    ids = extract(request, response)
    updated_ids = add(ids, product.id)
    response.set_cookie(COOKIE_NAME, json.dumps(updated_ids), httponly=True)


# Receivers

@receiver(product_viewed)
def receive_product_view(sender, product, user, request, response, **kwargs):
    """
    Receiver to handle viewing single product pages

    Requires the request and response objects due to dependence on cookies
    """
    return update(product, request, response)
