# This is a rewrite of django-sorting but with added support for i18n title
# strings.
# See https://github.com/directeur/django-sorting

from django import template
from django.conf import settings

register = template.Library()

DEFAULT_SORT_UP = getattr(
    settings, 'DEFAULT_SORT_UP',
    '<i class="icon-chevron-up"></i>')
DEFAULT_SORT_DOWN = getattr(
    settings, 'DEFAULT_SORT_DOWN',
    '<i class="icon-chevron-down"></i>')

sort_directions = {
    'asc': {'icon': DEFAULT_SORT_UP, 'inverse': 'desc'},
    'desc': {'icon': DEFAULT_SORT_DOWN, 'inverse': 'asc'},
    '': {'icon': DEFAULT_SORT_UP, 'inverse': 'desc'},
}


@register.tag
def anchor(parser, token):
    """
    Render an anchor tag with the appropriate ``href`` attribute for sorting on a given field.

    Usage:

    .. code-block:: html+django

        {% anchor query_param title %}

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``query_param``      The query parameter to use with key ``sort`` in the
                         generated URL.
    ``title``            The text to include in the anchor tag.
    ===================  =====================================================

    For example, on URL ``/dashboard/orders/``, including:

    .. code-block:: html+django

        {% anchor 'number' _("Order number") %}

    will render:

    .. code-block:: html+django

        <a href="/dashboard/orders/?sort=number">Order number</a>

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=anchor+path%3A%2Foscar%2Ftemplates&type=Code
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            "anchor tag takes at least 1 argument")
    try:
        title = bits[2]
    except IndexError:
        title = bits[1].capitalize()
    return SortAnchorNode(bits[1].strip(), title.strip())


class SortAnchorNode(template.Node):
    def __init__(self, field, title):
        self.field = template.Variable(field)
        self.title = template.Variable(title)

    def render(self, context):
        field = self.field.resolve(context)
        title = self.title.resolve(context)

        request = context['request']
        get_vars = request.GET.copy()
        sort_field = get_vars.pop('sort', [None])[0]

        icon = ''
        if sort_field == field:
            # We are already sorting on this field, so we set the inverse
            # direction within the GET params that get used within the href.
            direction = get_vars.pop('dir', [''])[0]
            get_vars['dir'] = sort_directions[direction]['inverse']
            icon = sort_directions[direction]['icon']

        href = u'%s?sort=%s' % (request.path, field)
        if len(get_vars) > 0:
            href += "&%s" % get_vars.urlencode()
        if icon:
            title = u"%s %s" % (title, icon)
        return u'<a href="%s">%s</a>' % (href, title)
