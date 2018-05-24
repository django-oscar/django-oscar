from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomerConfig(AppConfig):
    label = 'customer'
    name = 'oscar.apps.customer'
    verbose_name = _('Customer')

    def ready(self):
        from . import receivers  # noqa
        from .alerts import receivers  # noqa
