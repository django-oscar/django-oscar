from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig


class AnalyticsConfig(OscarConfig):
    label = "analytics"
    name = "oscar.apps.analytics"
    verbose_name = _("Analytics")

    # pylint: disable=unused-import
    def ready(self):
        from . import receivers
