from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class BasketConfig(OscarConfig):
    label = 'basket'
    name = 'oscar.apps.basket'
    verbose_name = _('Basket')

    namespace = 'basket'

    def ready(self):
        self.summary_view = get_class('basket.views', 'BasketView')
        self.saved_view = get_class('basket.views', 'SavedView')
        self.add_view = get_class('basket.views', 'BasketAddView')
        self.add_voucher_view = get_class('basket.views', 'VoucherAddView')
        self.remove_voucher_view = get_class('basket.views', 'VoucherRemoveView')

    def get_urls(self):
        urls = [
            url(r'^$', self.summary_view.as_view(), name='summary'),
            url(r'^add/(?P<pk>\d+)/$', self.add_view.as_view(), name='add'),
            url(r'^vouchers/add/$', self.add_voucher_view.as_view(),
                name='vouchers-add'),
            url(r'^vouchers/(?P<pk>\d+)/remove/$',
                self.remove_voucher_view.as_view(), name='vouchers-remove'),
            url(r'^saved/$', login_required(self.saved_view.as_view()),
                name='saved'),
        ]
        return self.post_process_urls(urls)
