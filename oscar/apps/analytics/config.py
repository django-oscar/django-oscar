from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    label = 'analytics'
    name = 'oscar.apps.analytics'

    def ready(self):
        from . import receivers  # noqa
