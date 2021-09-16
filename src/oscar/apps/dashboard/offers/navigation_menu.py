from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Offers"), icon="fas fa-bullhorn").add_child(Menu(
    label=_("Offers"), url_name="dashboard:offer-list")))
