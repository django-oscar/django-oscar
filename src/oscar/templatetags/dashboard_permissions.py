import logging
from django import template
from django.apps import apps
from oscar.core.loading import get_class

register = template.Library()
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")
logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def has_dashboard_permission(context, section, app_label):
    """Check if the user has the required dashboard permissions."""
    user = context["user"]

    try:
        app_config = apps.get_app_config(app_label)
        getattr(app_config, "configure_permissions", lambda: None)()
        required_perms = getattr(app_config, "permissions_map", {}).get(section, [])
    except LookupError:
        required_perms = []

    if not required_perms:
        return False

    # Single list of permissions
    if all(isinstance(perm, str) for perm in required_perms):
        result = all(user.has_perm(perm) for perm in required_perms)
    else:
        # Tuple/list of lists: ANY group satisfied (partner_dashboard_access)
        result = any(
            all(user.has_perm(perm) for perm in perm_group)
            for perm_group in required_perms
        )
    return result
