from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Vouchers"), identifier="vouchers", url_name="dashboard:voucher-list"),
                        parent_id="offers")
register_dashboard_menu(
    Menu(label=_("Vouchers Sets"), identifier="vouchers_sets", url_name="dashboard:voucher-set-list"),
    parent_id="offers")
