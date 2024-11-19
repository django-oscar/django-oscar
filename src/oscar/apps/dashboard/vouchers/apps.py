from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class VouchersDashboardConfig(OscarDashboardConfig):
    label = "vouchers_dashboard"
    name = "oscar.apps.dashboard.vouchers"
    verbose_name = _("Vouchers dashboard")

    default_permissions = [
        "is_staff",
    ]

    def configure_permissions(self):
        DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")

        self.permissions_map = {
            "voucher-list": DashboardPermission.voucher,
            "voucher-create": DashboardPermission.voucher,
            "voucher-update": DashboardPermission.voucher,
            "voucher-delete": DashboardPermission.voucher,
            "voucher-stats": DashboardPermission.voucher,
            "voucher-set-list": DashboardPermission.voucher,
            "voucher-set-create": DashboardPermission.voucher,
            "voucher-set-update": DashboardPermission.voucher,
            "voucher-set-detail": DashboardPermission.voucher,
            "voucher-set-download": DashboardPermission.voucher,
            "voucher-set-delete": DashboardPermission.voucher,
        }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.list_view = get_class("dashboard.vouchers.views", "VoucherListView")
        self.create_view = get_class("dashboard.vouchers.views", "VoucherCreateView")
        self.update_view = get_class("dashboard.vouchers.views", "VoucherUpdateView")
        self.delete_view = get_class("dashboard.vouchers.views", "VoucherDeleteView")
        self.stats_view = get_class("dashboard.vouchers.views", "VoucherStatsView")

        self.set_list_view = get_class("dashboard.vouchers.views", "VoucherSetListView")
        self.set_create_view = get_class(
            "dashboard.vouchers.views", "VoucherSetCreateView"
        )
        self.set_update_view = get_class(
            "dashboard.vouchers.views", "VoucherSetUpdateView"
        )
        self.set_detail_view = get_class(
            "dashboard.vouchers.views", "VoucherSetDetailView"
        )
        self.set_download_view = get_class(
            "dashboard.vouchers.views", "VoucherSetDownloadView"
        )
        self.set_delete_view = get_class(
            "dashboard.vouchers.views", "VoucherSetDeleteView"
        )
        self.configure_permissions()

    def get_urls(self):
        urls = [
            path("", self.list_view.as_view(), name="voucher-list"),
            path("create/", self.create_view.as_view(), name="voucher-create"),
            path("update/<int:pk>/", self.update_view.as_view(), name="voucher-update"),
            path("delete/<int:pk>/", self.delete_view.as_view(), name="voucher-delete"),
            path("stats/<int:pk>/", self.stats_view.as_view(), name="voucher-stats"),
            path("sets/", self.set_list_view.as_view(), name="voucher-set-list"),
            path(
                "sets/create/",
                self.set_create_view.as_view(),
                name="voucher-set-create",
            ),
            path(
                "sets/update/<int:pk>/",
                self.set_update_view.as_view(),
                name="voucher-set-update",
            ),
            path(
                "sets/detail/<int:pk>/",
                self.set_detail_view.as_view(),
                name="voucher-set-detail",
            ),
            path(
                "sets/download/<int:pk>/",
                self.set_download_view.as_view(),
                name="voucher-set-download",
            ),
            path(
                "sets/delete/<int:pk>/",
                self.set_delete_view.as_view(),
                name="voucher-set-delete",
            ),
        ]
        return self.post_process_urls(urls)
