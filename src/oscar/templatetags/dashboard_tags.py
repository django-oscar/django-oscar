from django import template
from django.conf import settings

from oscar.core.loading import get_class

get_nodes = get_class("dashboard.menu", "get_nodes")
register = template.Library()


@register.simple_tag
def dashboard_navigation(user):
    return get_nodes(user)



@register.simple_tag
def dashboard_settings_navigation():
    return settings.DASHBOARD_SETTINGS_CHILDREN