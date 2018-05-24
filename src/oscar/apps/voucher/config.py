from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VoucherConfig(AppConfig):
    label = 'voucher'
    name = 'oscar.apps.voucher'
    verbose_name = _('Voucher')

    def ready(self):
        from . import receivers  # noqa
