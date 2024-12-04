from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class ReviewsDashboardConfig(OscarDashboardConfig):
    label = "reviews_dashboard"
    name = "oscar.apps.dashboard.reviews"
    verbose_name = _("Reviews dashboard")

    default_permissions = [
        "is_staff",
    ]

    def configure_permissions(self):
        DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")

        self.permissions_map = {
            "reviews-list": DashboardPermission.get("product_review"),
            "reviews-update": DashboardPermission.get("product_review"),
            "reviews-delete": DashboardPermission.get("product_review"),
        }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.list_view = get_class("dashboard.reviews.views", "ReviewListView")
        self.update_view = get_class("dashboard.reviews.views", "ReviewUpdateView")
        self.delete_view = get_class("dashboard.reviews.views", "ReviewDeleteView")
        self.configure_permissions()

    def get_urls(self):
        urls = [
            path("", self.list_view.as_view(), name="reviews-list"),
            path("<int:pk>/", self.update_view.as_view(), name="reviews-update"),
            path("<int:pk>/delete/", self.delete_view.as_view(), name="reviews-delete"),
        ]
        return self.post_process_urls(urls)
