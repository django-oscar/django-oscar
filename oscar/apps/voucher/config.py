from django.apps import AppConfig

from oscar.apps.voucher import receivers


class VoucherConfig(AppConfig):
    app_label = 'voucher'
    name = 'oscar.apps.voucher'

    def ready(self):
        receivers.register()
        super(VoucherConfig, self).ready()
