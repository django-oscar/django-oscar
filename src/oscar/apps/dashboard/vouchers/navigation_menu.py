from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

_parent_id = _("offers")
register_dashboard_menu(Menu(label=_("Vouchers"), url_name="dashboard:voucher-list"), parent_id=_parent_id)
register_dashboard_menu(Menu(label=_("Vouchers Sets"), url_name="dashboard:voucher-set-list"), parent_id=_parent_id)
