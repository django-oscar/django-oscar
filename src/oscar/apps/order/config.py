from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrderConfig(AppConfig):
    label = 'order'
    name = 'oscar.apps.order'
    verbose_name = _('Order')
