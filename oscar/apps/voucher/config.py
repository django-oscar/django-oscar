from django.apps import AppConfig


class VoucherConfig(AppConfig):
    label = 'voucher'
    name = 'oscar.apps.voucher'

    def ready(self):
        from . import receivers  # noqa
