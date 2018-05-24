from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BasketConfig(AppConfig):
    label = 'basket'
    name = 'oscar.apps.basket'
    verbose_name = _('Basket')
