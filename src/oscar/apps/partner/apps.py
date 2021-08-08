from django.utils.translation import gettext_lazy as _

from oscar.core import application


class PartnerConfig(application.OscarConfig):
    label = 'partner'
    name = 'oscar.apps.partner'
    verbose_name = _('Partner')

    def ready(self):
        from . import receivers  # noqa
