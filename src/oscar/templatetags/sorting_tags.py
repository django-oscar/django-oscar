# This is a rewrite of django-sorting but with added support for i18n title
# strings.
# See https://github.com/directeur/django-sorting

from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

DEFAULT_SORT_UP = getattr(
    settings, 'DEFAULT_SORT_UP',
    '<i class="fas fa-chevron-up"></i>')
DEFAULT_SORT_DOWN = getattr(
    settings, 'DEFAULT_SORT_DOWN',
    '<i class="fas fa-chevron-down"></i>')

sort_directions = {
    'asc': {'icon': DEFAULT_SORT_UP, 'inverse': 'desc'},
    'desc': {'icon': DEFAULT_SORT_DOWN, 'inverse': 'asc'},
    '': {'icon': DEFAULT_SORT_UP, 'inverse': 'desc'},
}


@register.simple_tag(takes_context=True)
def anchor(context, field, title=None):
    field = field.strip()
    if title is None:
        title = field.capitalize()
    title = title.strip()
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
    icon = mark_safe(icon)

    href = '%s?sort=%s' % (request.path, field)
    if len(get_vars) > 0:
        href += "&%s" % get_vars.urlencode()
    if icon:
        title = format_html("{} {}", title, icon)
    return format_html('<a href="{}">{}</a>', mark_safe(href), title)
