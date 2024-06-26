from django.utils.translation import gettext_lazy as _

from oscar.navigation_menu_registry import Menu, register_dashboard_menu

register_dashboard_menu(Menu(label=_("Catalogue"), identifier="catalogue", icon="fas fa-sitemap").add_children(
    [
        Menu(label=_("Products"), identifier="products", url_name="dashboard:catalogue-product-list"),
        Menu(label=_("Product Types"), identifier="product_types", url_name="dashboard:catalogue-class-list"),
        Menu(label=_("Categories"), identifier="categories", url_name="dashboard:catalogue-category-list"),
        Menu(label=_("Low stock alerts"), identifier="low_stock_alerts", url_name="dashboard:stock-alert-list"),
        Menu(label=_("Options"), identifier="options", url_name="dashboard:catalogue-option-list"),
    ]
))
