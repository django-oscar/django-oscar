from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    app_label = 'analytics'
    name = 'oscar.apps.analytics'

    def ready(self):
        from .receivers import *  # noqa
        return super(AnalyticsConfig, self).ready()
