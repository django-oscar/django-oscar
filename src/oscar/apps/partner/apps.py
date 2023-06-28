from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig


class PartnerConfig(OscarConfig):
    label = "partner"
    name = "oscar.apps.partner"
    verbose_name = _("Partner")

    # pylint: disable=unused-import
    def ready(self):
        from . import receivers
