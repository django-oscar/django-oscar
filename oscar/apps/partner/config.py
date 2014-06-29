from django.apps import AppConfig


class PartnerConfig(AppConfig):
    label = 'partner'
    name = 'oscar.apps.partner'

    def ready(self):
        from . import receivers  # noqa
