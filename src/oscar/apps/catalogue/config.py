from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CatalogueConfig(AppConfig):
    label = 'catalogue'
    name = 'oscar.apps.catalogue'
    verbose_name = _('Catalogue')

    def ready(self):
        from . import receivers  # noqa
