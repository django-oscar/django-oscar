from django import template
from oscar.core.loading import get_class

register = template.Library()

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


@register.simple_tag(takes_context=True)
def has_dashboard_permission(context, section):
    """
    Template tag to check if the current user has required Django permissions
    for a given dashboard section.
    """
    user = context["user"]
    required_perms = DashboardPermission.permissions.get(section, [])
    perms_to_check = [perm for perm in required_perms if perm != "is_staff"]
    return all(user.has_perm(perm) for perm in perms_to_check)
