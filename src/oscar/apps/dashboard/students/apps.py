from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class StudentsDashboardConfig(OscarDashboardConfig):
    label = "students_dashboard"
    name = "oscar.apps.dashboard.students"
    verbose_name = _("Students dashboard")

    default_permissions = [
        "is_staff",
    ]
    permissions_map = {
        "students-list": (["is_staff"], ["partner.dashboard_access"]),
        "student-detail": (["is_staff"], ["partner.dashboard_access"]),
        "student-update": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.student_list_view = get_class("dashboard.students.views", "StudentListView")
        self.student_detail_view = get_class("dashboard.students.views", "StudentDetailView")
        self.student_update_view = get_class("dashboard.students.views", "StudentDetailView")


    def get_urls(self):
        urls = [
            path("", self.student_list_view.as_view(), name="students-list"),
            path(
                "<str:national_id>/", self.student_detail_view.as_view(), name="student-detail"
            ),
            path('<str:national_id>/update/', self.student_update_view.as_view(), name='student-update'),
        ]
        return self.post_process_urls(urls)
