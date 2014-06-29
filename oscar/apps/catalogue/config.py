from django.apps import AppConfig


class CatalogueConfig(AppConfig):
    app_label = 'catalogue'
    name = 'oscar.apps.catalogue'

    def ready(self):
        from .receivers import *  # noqa
        return super(CatalogueConfig, self).ready()
