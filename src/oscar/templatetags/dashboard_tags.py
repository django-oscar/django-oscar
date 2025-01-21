from django import template
from django.conf import settings

from oscar.core.loading import get_class

get_nodes = get_class("dashboard.menu", "get_nodes")
register = template.Library()


@register.simple_tag
def dashboard_navigation(user):
    if hasattr(user, "vendor"):
        return get_nodes(user)
    return get_nodes(user, settings.OSCAR_SCHOOLS_DASHBOARD_NAVIGATION)



@register.simple_tag
def dashboard_settings_navigation():
    return settings.DASHBOARD_SETTINGS_CHILDREN