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
    permissions_map = _map = {
        "catalogue-product": (["is_staff"], ["partner.dashboard_access"]),
        "catalogue-product-create": (["is_staff"], ["partner.dashboard_access"]),
        "catalogue-product-list": (["is_staff"], ["partner.dashboard_access"]),
        "catalogue-product-delete": (["is_staff"], ["partner.dashboard_access"]),
        "catalogue-product-lookup": (["is_staff"], ["partner.dashboard_access"]),
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
