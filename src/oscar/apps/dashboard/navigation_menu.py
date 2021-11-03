from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(
    Menu(label=_("Dashboard"), identifier="dashboard", icon="fas fa-list", url_name="dashboard:index"))
register_dashboard_menu(Menu(label=_("Fulfilment"), identifier="fulfilment", icon="fas fa-shopping-card"))
