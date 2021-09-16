from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

_parent_id = _("fulfilment")
register_dashboard_menu(Menu(label=_("Orders"), url_name="dashboard:order-list"), parent_id=_parent_id)
register_dashboard_menu(Menu(label=_("Statistics"), url_name="dashboard:order-stats"), parent_id=_parent_id)
