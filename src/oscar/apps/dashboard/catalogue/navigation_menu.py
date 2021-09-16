from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Catalogue"), icon="fas fa-sitemap").add_children(
    [
        Menu(label=_("Products"), url_name="dashboard:catalogue-product-list"),
        Menu(label=_("Product Types"), url_name="dashboard:catalogue-class-list"),
        Menu(label=_("Categories"), url_name="dashboard:catalogue-category-list"),
        Menu(label=_("Low stock alerts"), url_name="dashboard:stock-alert-list"),
        Menu(label=_("Options"), url_name="dashboard:catalogue-option-list"),
    ]
))
