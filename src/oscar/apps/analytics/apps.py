from django.utils.translation import gettext_lazy as _

from oscar.core import application


class AnalyticsConfig(application.OscarConfig):
    label = 'analytics'
    name = 'oscar.apps.analytics'
    verbose_name = _('Analytics')

    def ready(self):
        from . import receivers  # noqa
