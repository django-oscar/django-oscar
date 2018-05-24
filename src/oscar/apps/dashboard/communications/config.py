from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommunicationsDashboardConfig(AppConfig):
    label = 'communications_dashboard'
    name = 'oscar.apps.dashboard.communications'
    verbose_name = _('Communications dashboard')
