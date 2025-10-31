"""Permissions used for different dashboard views."""

from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardPermission:
    """Permissions used for different dashboard views."""

    # Only custom overrides. No standard permissions needed here.
    permissions = {}
    staff = ["is_staff"]
    # Partner Access
    partner_dashboard_access = ["partner.dashboard_access"]

    @classmethod
    def get(cls, app_label, *codenames):
        """
        Get permissions for given app_label and codenames.
        Supports both explicit mappings and auto-generated permissions.
        """
        permissions = set()

        for codename in codenames:
            key = codename
            if key in cls.permissions:
                permissions.update(cls.permissions[key])
            else:
                permissions.add(f"{app_label}.{codename}")

        return list(permissions)
