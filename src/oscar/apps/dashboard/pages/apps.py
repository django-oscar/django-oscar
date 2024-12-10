from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PagesDashboardConfig(OscarDashboardConfig):
    label = "pages_dashboard"
    name = "oscar.apps.dashboard.pages"
    verbose_name = _("Pages dashboard")

    default_permissions = [
        "is_staff",
    ]

    def configure_permissions(self):
        DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")

        self.permissions_map = {
            "page-list": DashboardPermission.get("flat_page"),
            "page-create": DashboardPermission.get("flat_page"),
            "page-update": DashboardPermission.get("flat_page"),
            "page-delete": DashboardPermission.get("flat_page"),
        }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.list_view = get_class("dashboard.pages.views", "PageListView")
        self.create_view = get_class("dashboard.pages.views", "PageCreateView")
        self.update_view = get_class("dashboard.pages.views", "PageUpdateView")
        self.delete_view = get_class("dashboard.pages.views", "PageDeleteView")
        self.configure_permissions()

    def get_urls(self):
        """
        Get URL patterns defined for flatpage management application.
        """
        urls = [
            path("", self.list_view.as_view(), name="page-list"),
            path("create/", self.create_view.as_view(), name="page-create"),
            path("update/<str:pk>/", self.update_view.as_view(), name="page-update"),
            path("delete/<str:pk>/", self.delete_view.as_view(), name="page-delete"),
        ]
        return self.post_process_urls(urls)
