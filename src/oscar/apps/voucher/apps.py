from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class VoucherConfig(OscarConfig):
    label = 'voucher'
    name = 'oscar.apps.voucher'
    verbose_name = _('Voucher')

    def ready(self):
        from . import receivers  # noqa
        from . import signals  # noqa

        self.add_voucher_view = get_class('voucher.views', 'VoucherAddView')
        self.remove_voucher_view = get_class('voucher.views', 'VoucherRemoveView')

    def get_urls(self):
        urls = [
            path('add/', self.add_voucher_view.as_view(), name='vouchers-add'),
            path('<int:pk>/remove/', self.remove_voucher_view.as_view(), name='vouchers-remove'),
        ]
        return self.post_process_urls(urls)
