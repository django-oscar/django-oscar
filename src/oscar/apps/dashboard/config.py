from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DashboardConfig(AppConfig):
    label = 'dashboard'
    name = 'oscar.apps.dashboard'
    verbose_name = _('Dashboard')
