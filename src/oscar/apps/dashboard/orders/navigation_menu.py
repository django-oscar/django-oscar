from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Orders"), identifier="orders", url_name="dashboard:order-list"),
                        parent_id="fulfilment")
register_dashboard_menu(Menu(label=_("Statistics"), identifier="statistics", url_name="dashboard:order-stats"),
                        parent_id="fulfilment")
