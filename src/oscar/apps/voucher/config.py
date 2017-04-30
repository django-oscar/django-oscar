from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class VoucherConfig(AppConfig):
    label = 'voucher'
    name = 'oscar.apps.voucher'
    verbose_name = _('Voucher')

    def ready(self):
        from . import receivers  # noqa
