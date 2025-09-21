from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class CatalogueDashboardConfig(OscarDashboardConfig):
    label = "catalogue_dashboard"
    name = "oscar.apps.dashboard.catalogue"
    verbose_name = _("Catalogue")

    default_permissions = [
        "is_staff",
    ]

    def configure_permissions(self):
        DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")

        self.permissions_map = {
            # Product views
            "catalogue-product": (
                DashboardPermission.get(
                    "catalogue", "view_product", "add_product", "change_product"
                ),
                DashboardPermission.partner_dashboard_access,
            ),
            "catalogue-product-create": (
                DashboardPermission.get("catalogue", "view_product", "add_product"),
                DashboardPermission.partner_dashboard_access,
            ),
            "catalogue-product-list": (
                DashboardPermission.get("catalogue", "view_product"),
                DashboardPermission.partner_dashboard_access,
            ),
            "catalogue-product-delete": (
                DashboardPermission.get("catalogue", "delete_product"),
                DashboardPermission.partner_dashboard_access,
            ),
            "catalogue-product-lookup": (
                DashboardPermission.get("catalogue", "view_product"),
                DashboardPermission.partner_dashboard_access,
            ),
            "catalogue-product-create-child": DashboardPermission.get(
                "catalogue", "view_product", "add_product"
            ),
            # Stock alerts
            "stock-alert-list": DashboardPermission.get("partner", "view_stockalert"),
            # Category views
            "catalogue-category-list": DashboardPermission.get(
                "catalogue", "view_category"
            ),
            "catalogue-category-detail-list": DashboardPermission.get(
                "catalogue", "view_category"
            ),
            "catalogue-category-create": DashboardPermission.get(
                "catalogue", "add_category"
            ),
            "catalogue-category-create-child": DashboardPermission.get(
                "catalogue", "add_category"
            ),
            "catalogue-category-update": DashboardPermission.get(
                "catalogue", "change_category"
            ),
            "catalogue-category-delete": DashboardPermission.get(
                "catalogue", "delete_category"
            ),
            # Product class views
            "catalogue-class-create": DashboardPermission.get(
                "catalogue", "add_productclass"
            ),
            "catalogue-class-list": DashboardPermission.get(
                "catalogue", "view_productclass"
            ),
            "catalogue-class-update": DashboardPermission.get(
                "catalogue", "change_productclass"
            ),
            "catalogue-class-delete": DashboardPermission.get(
                "catalogue", "delete_productclass"
            ),
            # Attribute option group views
            "catalogue-attribute-option-group-list": DashboardPermission.get(
                "catalogue", "view_attributeoptiongroup"
            ),
            "catalogue-attribute-option-group-create": DashboardPermission.get(
                "catalogue", "view_attributeoptiongroup", "add_attributeoptiongroup"
            ),
            "catalogue-attribute-option-group-update": DashboardPermission.get(
                "catalogue", "view_attributeoptiongroup", "change_attributeoptiongroup"
            ),
            "catalogue-attribute-option-group-delete": DashboardPermission.get(
                "catalogue", "view_attributeoptiongroup", "delete_attributeoptiongroup"
            ),
            # Option views
            "catalogue-option-list": DashboardPermission.get(
                "catalogue", "view_option"
            ),
            "catalogue-option-create": DashboardPermission.get(
                "catalogue", "view_option", "add_option"
            ),
            "catalogue-option-update": DashboardPermission.get(
                "catalogue", "view_option", "change_option"
            ),
            "catalogue-option-delete": DashboardPermission.get(
                "catalogue", "view_option", "delete_option"
            ),
        }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.product_list_view = get_class(
            "dashboard.catalogue.views", "ProductListView"
        )
        self.product_lookup_view = get_class(
            "dashboard.catalogue.views", "ProductLookupView"
        )
        self.product_create_redirect_view = get_class(
            "dashboard.catalogue.views", "ProductCreateRedirectView"
        )
        self.product_createupdate_view = get_class(
            "dashboard.catalogue.views", "ProductCreateUpdateView"
        )
        self.product_delete_view = get_class(
            "dashboard.catalogue.views", "ProductDeleteView"
        )

        self.product_class_create_view = get_class(
            "dashboard.catalogue.views", "ProductClassCreateView"
        )
        self.product_class_update_view = get_class(
            "dashboard.catalogue.views", "ProductClassUpdateView"
        )
        self.product_class_list_view = get_class(
            "dashboard.catalogue.views", "ProductClassListView"
        )
        self.product_class_delete_view = get_class(
            "dashboard.catalogue.views", "ProductClassDeleteView"
        )

        self.category_list_view = get_class(
            "dashboard.catalogue.views", "CategoryListView"
        )
        self.category_detail_list_view = get_class(
            "dashboard.catalogue.views", "CategoryDetailListView"
        )
        self.category_create_view = get_class(
            "dashboard.catalogue.views", "CategoryCreateView"
        )
        self.category_update_view = get_class(
            "dashboard.catalogue.views", "CategoryUpdateView"
        )
        self.category_delete_view = get_class(
            "dashboard.catalogue.views", "CategoryDeleteView"
        )

        self.stock_alert_view = get_class(
            "dashboard.catalogue.views", "StockAlertListView"
        )

        self.attribute_option_group_create_view = get_class(
            "dashboard.catalogue.views", "AttributeOptionGroupCreateView"
        )
        self.attribute_option_group_list_view = get_class(
            "dashboard.catalogue.views", "AttributeOptionGroupListView"
        )
        self.attribute_option_group_update_view = get_class(
            "dashboard.catalogue.views", "AttributeOptionGroupUpdateView"
        )
        self.attribute_option_group_delete_view = get_class(
            "dashboard.catalogue.views", "AttributeOptionGroupDeleteView"
        )

        self.option_list_view = get_class("dashboard.catalogue.views", "OptionListView")
        self.option_create_view = get_class(
            "dashboard.catalogue.views", "OptionCreateView"
        )
        self.option_update_view = get_class(
            "dashboard.catalogue.views", "OptionUpdateView"
        )
        self.option_delete_view = get_class(
            "dashboard.catalogue.views", "OptionDeleteView"
        )
        self.configure_permissions()

    def get_urls(self):
        urls = [
            path(
                "products/<int:pk>/",
                self.product_createupdate_view.as_view(),
                name="catalogue-product",
            ),
            path(
                "products/create/",
                self.product_create_redirect_view.as_view(),
                name="catalogue-product-create",
            ),
            re_path(
                r"^products/create/(?P<product_class_slug>[\w-]+)/$",
                self.product_createupdate_view.as_view(),
                name="catalogue-product-create",
            ),
            path(
                "products/<int:parent_pk>/create-variant/",
                self.product_createupdate_view.as_view(),
                name="catalogue-product-create-child",
            ),
            path(
                "products/<int:pk>/delete/",
                self.product_delete_view.as_view(),
                name="catalogue-product-delete",
            ),
            path("", self.product_list_view.as_view(), name="catalogue-product-list"),
            path(
                "stock-alerts/",
                self.stock_alert_view.as_view(),
                name="stock-alert-list",
            ),
            path(
                "product-lookup/",
                self.product_lookup_view.as_view(),
                name="catalogue-product-lookup",
            ),
            path(
                "categories/",
                self.category_list_view.as_view(),
                name="catalogue-category-list",
            ),
            path(
                "categories/<int:pk>/",
                self.category_detail_list_view.as_view(),
                name="catalogue-category-detail-list",
            ),
            path(
                "categories/create/",
                self.category_create_view.as_view(),
                name="catalogue-category-create",
            ),
            path(
                "categories/create/<int:parent>/",
                self.category_create_view.as_view(),
                name="catalogue-category-create-child",
            ),
            path(
                "categories/<int:pk>/update/",
                self.category_update_view.as_view(),
                name="catalogue-category-update",
            ),
            path(
                "categories/<int:pk>/delete/",
                self.category_delete_view.as_view(),
                name="catalogue-category-delete",
            ),
            path(
                "product-type/create/",
                self.product_class_create_view.as_view(),
                name="catalogue-class-create",
            ),
            path(
                "product-types/",
                self.product_class_list_view.as_view(),
                name="catalogue-class-list",
            ),
            path(
                "product-type/<int:pk>/update/",
                self.product_class_update_view.as_view(),
                name="catalogue-class-update",
            ),
            path(
                "product-type/<int:pk>/delete/",
                self.product_class_delete_view.as_view(),
                name="catalogue-class-delete",
            ),
            path(
                "attribute-option-group/create/",
                self.attribute_option_group_create_view.as_view(),
                name="catalogue-attribute-option-group-create",
            ),
            path(
                "attribute-option-group/",
                self.attribute_option_group_list_view.as_view(),
                name="catalogue-attribute-option-group-list",
            ),
            # The RelatedFieldWidgetWrapper code does something funny with
            # placeholder urls, so it does need to match more than just a pk
            path(
                "attribute-option-group/<str:pk>/update/",
                self.attribute_option_group_update_view.as_view(),
                name="catalogue-attribute-option-group-update",
            ),
            # The RelatedFieldWidgetWrapper code does something funny with
            # placeholder urls, so it does need to match more than just a pk
            path(
                "attribute-option-group/<str:pk>/delete/",
                self.attribute_option_group_delete_view.as_view(),
                name="catalogue-attribute-option-group-delete",
            ),
            path(
                "option/", self.option_list_view.as_view(), name="catalogue-option-list"
            ),
            path(
                "option/create/",
                self.option_create_view.as_view(),
                name="catalogue-option-create",
            ),
            path(
                "option/<str:pk>/update/",
                self.option_update_view.as_view(),
                name="catalogue-option-update",
            ),
            path(
                "option/<str:pk>/delete/",
                self.option_delete_view.as_view(),
                name="catalogue-option-delete",
            ),
        ]
        return self.post_process_urls(urls)
