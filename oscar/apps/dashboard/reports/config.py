from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ReportsDashboardConfig(AppConfig):
    label = 'reports_dashboard'
    name = 'oscar.apps.dashboard.reports'
    verbose_name = _('Reports dashboard')
