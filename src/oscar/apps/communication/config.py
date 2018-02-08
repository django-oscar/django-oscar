from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommunicationConfig(AppConfig):
    label = 'communication'
    name = 'oscar.apps.communication'
    verbose_name = _('Communication')

    def ready(self):
        from .alerts import receivers  # noqa
