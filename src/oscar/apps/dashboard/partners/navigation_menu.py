from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Partners"), identifier="partners", url_name="dashboard:partner-list"),
                        parent_id="fulfilment")
