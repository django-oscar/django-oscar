from urllib import parse

from django import template
from django.urls import Resolver404, resolve
from django.utils.translation import gettext_lazy as _

from oscar.apps.customer import history
from oscar.core.loading import get_model

Site = get_model('sites', 'Site')

register = template.Library()


@register.inclusion_tag('customer/history/recently_viewed_products.html',
                        takes_context=True)
def recently_viewed_products(context, current_product=None):
    """
    Inclusion tag listing the most recently viewed products
    """
    request = context['request']
    products = history.get(request)
    if current_product:
        products = [p for p in products if p != current_product]
    return {'products': products,
            'request': request}


@register.simple_tag(takes_context=True)  # noqa (too complex (11))
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
        url = parse.urlparse(referrer)
    except (ValueError, TypeError):
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

    return {'url': referrer, 'title': str(title), 'match': match}
