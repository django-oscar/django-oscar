from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AnalyticsConfig(AppConfig):
    label = 'analytics'
    name = 'oscar.apps.analytics'
    verbose_name = _('Analytics')

    def ready(self):
        from . import receivers  # noqa
