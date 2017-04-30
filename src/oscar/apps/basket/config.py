from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class BasketConfig(AppConfig):
    label = 'basket'
    name = 'oscar.apps.basket'
    verbose_name = _('Basket')
