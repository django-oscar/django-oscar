from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SystemConfig(AppConfig):
    label = 'system'
    name = 'oscar.apps.system'
    verbose_name = _('System')
