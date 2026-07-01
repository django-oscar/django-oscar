from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class ShippingDashboardConfig(OscarDashboardConfig):
    label = "shipping_dashboard"
    name = "oscar.apps.dashboard.shipping"
    verbose_name = _("Shipping dashboard")

    default_permissions = ["is_staff"]

    def configure_permissions(self):
        DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")

        self.permissions_map = {
            "shipping-method-list": DashboardPermission.get(
                "shipping", "view_weightbased"
            ),
            "shipping-method-create": DashboardPermission.get(
                "shipping", "view_weightbased", "add_weightbased"
            ),
            "shipping-method-detail": DashboardPermission.get(
                "shipping", "view_weightbased"
            ),
            "shipping-method-edit": DashboardPermission.get(
                "shipping", "view_weightbased", "change_weightbased"
            ),
            "shipping-method-delete": DashboardPermission.get(
                "shipping", "view_weightbased", "delete_weightbased"
            ),
            "shipping-method-band-edit": DashboardPermission.get(
                "shipping", "view_weightbased", "change_weightbased"
            ),
            "shipping-method-band-delete": DashboardPermission.get(
                "shipping", "view_weightbased", "delete_weightbased"
            ),
        }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.weight_method_list_view = get_class(
            "dashboard.shipping.views", "WeightBasedListView"
        )
        self.weight_method_create_view = get_class(
            "dashboard.shipping.views", "WeightBasedCreateView"
        )
        self.weight_method_edit_view = get_class(
            "dashboard.shipping.views", "WeightBasedUpdateView"
        )
        self.weight_method_delete_view = get_class(
            "dashboard.shipping.views", "WeightBasedDeleteView"
        )
        self.weight_method_detail_view = get_class(
            "dashboard.shipping.views", "WeightBasedDetailView"
        )
        self.weight_band_edit_view = get_class(
            "dashboard.shipping.views", "WeightBandUpdateView"
        )
        self.weight_band_delete_view = get_class(
            "dashboard.shipping.views", "WeightBandDeleteView"
        )
        self.configure_permissions()

    def get_urls(self):
        urlpatterns = [
            path(
                "weight-based/",
                self.weight_method_list_view.as_view(),
                name="shipping-method-list",
            ),
            path(
                "weight-based/create/",
                self.weight_method_create_view.as_view(),
                name="shipping-method-create",
            ),
            path(
                "weight-based/<int:pk>/",
                self.weight_method_detail_view.as_view(),
                name="shipping-method-detail",
            ),
            path(
                "weight-based/<int:pk>/edit/",
                self.weight_method_edit_view.as_view(),
                name="shipping-method-edit",
            ),
            path(
                "weight-based/<int:pk>/delete/",
                self.weight_method_delete_view.as_view(),
                name="shipping-method-delete",
            ),
            path(
                "weight-based/<int:method_pk>/bands/<int:pk>/",
                self.weight_band_edit_view.as_view(),
                name="shipping-method-band-edit",
            ),
            path(
                "weight-based/<int:method_pk>/bands/<int:pk>/delete/",
                self.weight_band_delete_view.as_view(),
                name="shipping-method-band-delete",
            ),
        ]
        return self.post_process_urls(urlpatterns)
