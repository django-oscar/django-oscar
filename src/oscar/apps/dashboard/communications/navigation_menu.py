from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Email templates"), url_name="dashboard:comms-list"), parent_id=_("content"))
