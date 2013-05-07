import urlparse

from django import template
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import resolve, Resolver404

from oscar.core.loading import get_class

Product = get_model('catalogue', 'Product')
Site = get_model('sites', 'Site')
get_recently_viewed_product_ids = get_class(
    'customer.history_helpers', 'get_recently_viewed_product_ids')

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
    if current_product and current_product.id in product_ids:
        product_ids.remove(current_product.id)

    # Reordering as the id order gets messed up in the query
    product_dict = Product.browsable.in_bulk(product_ids)
    product_ids.reverse()
    products = [product_dict[id] for id in product_ids if id in product_dict]
    return {'products': products,
            'request': request}


@register.assignment_tag(takes_context=True)
def get_back_button(context):
    """
    Show back button, custom title available for different urls, for
    example 'Back to search results', no back button if user came from other
    site
    """
    request = context.get('request', None)
    if not request:
        raise Exception('Cannot get request from context')

    referrer = request.META.get('HTTP_REFERER', None)
    if not referrer:
        return None

    try:
        url = urlparse.urlparse(referrer)
    except:
        return None

    if request.get_host() != url.netloc:
        try:
            Site.objects.get(domain=url.netloc)
        except Site.DoesNotExist:
            # Came from somewhere else, don't show back button:
            return None

    try:
        match = resolve(url.path)
    except Resolver404:
        return None

    # This dict can be extended to link back to other browsing pages
    titles = {
        'search:search': _('Back to search results'),
    }
    title = titles.get(match.view_name, None)

    if title is None:
        return None

    return {'url': referrer, 'title': unicode(title), 'match': match}
