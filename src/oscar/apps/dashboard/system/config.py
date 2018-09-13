from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SystemDashboardConfig(AppConfig):
    label = 'system_dashboard'
    name = 'oscar.apps.dashboard.system'
    verbose_name = _('System dashboard')

