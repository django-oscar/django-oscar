from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Customers"), identifier="customers", icon="fas fa-users").add_children(
    [
        Menu(label=_("Customers"), identifier="customers", url_name="dashboard:users-index"),
        Menu(label=_("Stock alert requests"), identifier="stock_alert_requests", url_name="dashboard:user-alert-list"),
    ],
))
