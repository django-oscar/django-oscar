from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CheckoutConfig(AppConfig):
    label = 'checkout'
    name = 'oscar.apps.checkout'
    verbose_name = _('Checkout')
