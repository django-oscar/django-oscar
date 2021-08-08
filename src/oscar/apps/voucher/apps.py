from django.utils.translation import gettext_lazy as _

from oscar.core import application


class VoucherConfig(application.OscarConfig):
    label = 'voucher'
    name = 'oscar.apps.voucher'
    verbose_name = _('Voucher')

    def ready(self):
        from . import receivers  # noqa
