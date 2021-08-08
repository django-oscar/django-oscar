from django.utils.translation import gettext_lazy as _

from oscar.core import application


class PaymentConfig(application.OscarConfig):
    label = 'payment'
    name = 'oscar.apps.payment'
    verbose_name = _('Payment')
