from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Ranges"), identifier="ranges", url_name="dashboard:range-list"),
                        parent_id="catalogue")
