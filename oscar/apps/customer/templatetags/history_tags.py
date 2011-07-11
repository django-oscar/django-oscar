from django import template

from oscar.core.loading import import_module
product_models = import_module('catalogue.models', ['Product', 'ProductClass'])
history_helpers = import_module('customer.history_helpers', ['get_recently_viewed_product_ids'])

register = template.Library()

@register.inclusion_tag('customer/history/recently-viewed-products.html', takes_context=True)
def recently_viewed_products(context):
    u"""
    Inclusion tag listing the most recently viewed products
    """
    request = context['request']
    product_ids = history_helpers.get_recently_viewed_product_ids(request)
    product_dict = product_models.Product.browsable.in_bulk(product_ids)
    
    # Reordering as the id order gets messed up in the query
    product_ids.reverse()
    products = [product_dict[id] for id in product_ids if id in product_dict]
    return {'products': products}