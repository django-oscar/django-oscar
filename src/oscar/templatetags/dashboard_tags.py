from django import template

from oscar.core.loading import get_class

get_nodes = get_class('dashboard.menu', 'get_nodes')
register = template.Library()


@register.simple_tag
def dashboard_navigation(user):
    return get_nodes(user)
