from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PagesDashboardConfig(AppConfig):
    label = 'pages_dashboard'
    name = 'oscar.apps.dashboard.pages'
    verbose_name = _('Pages dashboard')
