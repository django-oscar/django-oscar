from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(
    Menu(label=_("Reports"), identifier="reports", icon="fas fa-chart-bar", url_name="dashboard:reports-index"))
