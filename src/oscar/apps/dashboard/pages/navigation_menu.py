from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Content"), identifier="content", icon="fas fa-folder").add_child(Menu(
    label=_("Pages"), identifier="pages", url_name="dashboard:page-list")))
