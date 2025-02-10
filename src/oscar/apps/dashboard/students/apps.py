from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class StudentsDashboardConfig(OscarDashboardConfig):
    label = "students_dashboard"
    name = "oscar.apps.dashboard.students"
    verbose_name = _("Students dashboard")

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.student_list_view = get_class("dashboard.students.views", "StudentListView")
        self.student_detail_view = get_class("dashboard.students.views", "StudentDetailView")
        self.student_update_view = get_class("dashboard.students.views", "StudentUpdateView")
        self.student_create_view = get_class("dashboard.students.views", "StudentCreateView")
        # Fix: Use different attribute names for each import view
        self.student_import_view = get_class("dashboard.students.views", "StudentImportView")
        self.student_import_map_view = get_class("dashboard.students.views", "StudentImportMapFieldsView")
        self.student_import_preview_view = get_class("dashboard.students.views", "StudentImportPreviewView")
        self.student_import_success_view = get_class("dashboard.students.views", "StudentImportSuccessView")
        # Fix: Use get_class for the sample CSV view
        self.student_sample_csv_view = get_class("dashboard.students.views", "student_sample_csv_view")
        self.student_images_import_view = get_class(
            "dashboard.students.views", "StudentImagesImportView"
        )
        self.student_images_import_success_view = get_class(
            "dashboard.students.views", "StudentImagesImportSuccessView"
        )
        self.student_import_progress_view = get_class(
            "dashboard.students.views", "StudentImportProgressView"
        )
        # Import tasks to ensure they're registered
        from . import tasks
    def get_urls(self):
        urls = [
            path("", self.student_list_view.as_view(), name="students-list"),
            path(
                "<str:national_id>/details",
                self.student_detail_view.as_view(),
                name="student-detail",
            ),
            path(
                "<str:national_id>/update/",
                self.student_update_view.as_view(),
                name="student-update",
            ),
            path("create/", self.student_create_view.as_view(), name="student-create"),
            # Fix: Use the class attributes instead of direct references
            path("import/", self.student_import_view.as_view(), name="student-import"),
            path(
                "import/map/",
                self.student_import_map_view.as_view(),
                name="student-import-map",
            ),
            path(
                "import/preview/",
                self.student_import_preview_view.as_view(),
                name="student-import-preview",
            ),
            path(
                "import/success/",
                self.student_import_success_view.as_view(),
                name="student-import-success",
            ),
            path(
                "import/progress/",
                self.student_import_progress_view.as_view(),
                name="student-import-progress",
            ),
            path(
                "import/sample/",
                self.student_sample_csv_view,
                name="student-sample-csv",
            ),
            path(
                "import/photos/",
                self.student_images_import_view.as_view(),
                name="student-images-import",
            ),
            path(
                "import/photos/success/",
                self.student_images_import_success_view.as_view(),
                name="student-images-import-success",
            ),
        ]

        return self.post_process_urls(urls)
