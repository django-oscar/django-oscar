from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UsersDashboardConfig(AppConfig):
    label = 'users_dashboard'
    name = 'oscar.apps.dashboard.users'
    verbose_name = _('Users dashboard')
