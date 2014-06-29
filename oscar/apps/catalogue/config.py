from django.apps import AppConfig


class CatalogueConfig(AppConfig):
    label = 'catalogue'
    name = 'oscar.apps.catalogue'

    def ready(self):
        from . import receivers  # noqa
