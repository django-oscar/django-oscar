from django.dispatch import receiver

from oscar.core.loading import get_class

from . import history

product_viewed = get_class('catalogue.signals', 'product_viewed')


@receiver(product_viewed)
def receive_product_view(sender, product, user, request, response, **kwargs):
    """
    Receiver to handle viewing single product pages

    Requires the request and response objects due to dependence on cookies
    """
    return history.update(product, request, response)
