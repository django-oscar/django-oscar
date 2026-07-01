from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig


class CommunicationConfig(OscarConfig):
    label = "communication"
    name = "oscar.apps.communication"
    verbose_name = _("Communication")
