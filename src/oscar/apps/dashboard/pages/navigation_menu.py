from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Content"), icon="fas fa-folder").add_child(Menu(
    label=_("Pages"), url_name="dashboard:page-list")))
