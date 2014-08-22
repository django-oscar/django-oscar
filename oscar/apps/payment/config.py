from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PaymentConfig(AppConfig):
    label = 'payment'
    name = 'oscar.apps.payment'
    verbose_name = _('Payment')
