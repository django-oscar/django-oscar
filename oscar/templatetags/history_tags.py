import six
from six.moves.urllib import parse

from django import template
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import resolve, Resolver404

from oscar.core.loading import get_model
from oscar.apps.customer import history

Site = get_model('sites', 'Site')

register = template.Library()


@register.inclusion_tag('customer/history/recently_viewed_products.html',
                        takes_context=True)
def recently_viewed_products(context):
    """
    Include a list of the customer's recently viewed products.

    Usage:

    .. code-block:: html+django

        {% recently_viewed_products %}

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=recently_viewed_products+path%3A%2Foscar%2Ftemplates&type=Code
    """
    request = context['request']
    products = history.get(request)
    return {'products': products,
            'request': request}


@register.assignment_tag(takes_context=True)
def get_back_button(context):
    """
    Assign a dict of data for rendering a button that takes the user to the
    previous page (if on same site).

    Usage:

    .. code-block:: html+django

        {% get_back_button as back_button %}

        {% if back_button %}
            <a href="{{ back_button.url }}">{{ back_button.title }}</a>
        {% endif %}

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=get_back_button+path%3A%2Foscar%2Ftemplates&type=Code
    """
    request = context.get('request', None)
    if not request:
        raise Exception('Cannot get request from context')

    referrer = request.META.get('HTTP_REFERER', None)
    if not referrer:
        return None

    try:
        url = parse.urlparse(referrer)
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
