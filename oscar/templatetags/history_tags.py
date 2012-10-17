from django import template
from django.db.models import get_model

from oscar.core.loading import get_class

Product = get_model('catalogue', 'Product')
get_recently_viewed_product_ids = get_class('customer.history_helpers',
                                            'get_recently_viewed_product_ids')

register = template.Library()


@register.inclusion_tag('customer/history/recently_viewed_products.html',
                        takes_context=True)
def recently_viewed_products(context):
    """
    Inclusion tag listing the most recently viewed products
    """
    request = context['request']
    product_ids = get_recently_viewed_product_ids(request)

    current_product = context.get('product', None)
    if current_product.id in product_ids:
        product_ids.remove(current_product.id)

    # Reordering as the id order gets messed up in the query
    product_dict = Product.browsable.in_bulk(product_ids)
    product_ids.reverse()
    products = [product_dict[id] for id in product_ids if id in product_dict]
    return {'products': products,
            'request': request}
