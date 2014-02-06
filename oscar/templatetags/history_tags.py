import six
from django import template
from oscar.core.loading import get_model
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import resolve, Resolver404

from oscar.apps.customer import history
from oscar.core.compat import urlparse

Site = get_model('sites', 'Site')

register = template.Library()


@register.inclusion_tag('customer/history/recently_viewed_products.html',
                        takes_context=True)
def recently_viewed_products(context):
    """
    Inclusion tag listing the most recently viewed products
    """
    request = context['request']
    products = history.get(request)
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

    return {'url': referrer, 'title': six.text_type(title), 'match': match}
