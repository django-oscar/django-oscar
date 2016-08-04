from django.conf.urls import url

from oscar.core.application import DashboardApplication
from oscar.core.loading import get_class


class VoucherDashboardApplication(DashboardApplication):
    name = None
    default_permissions = ['is_staff', ]

    list_view = get_class('dashboard.vouchers.views', 'VoucherListView')
    create_view = get_class('dashboard.vouchers.views', 'VoucherCreateView')
    update_view = get_class('dashboard.vouchers.views', 'VoucherUpdateView')
    delete_view = get_class('dashboard.vouchers.views', 'VoucherDeleteView')
    stats_view = get_class('dashboard.vouchers.views', 'VoucherStatsView')

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='voucher-list'),
            url(r'^create/$', self.create_view.as_view(),
                name='voucher-create'),
            url(r'^update/(?P<pk>\d+)/$', self.update_view.as_view(),
                name='voucher-update'),
            url(r'^delete/(?P<pk>\d+)/$', self.delete_view.as_view(),
                name='voucher-delete'),
            url(r'^stats/(?P<pk>\d+)/$', self.stats_view.as_view(),
                name='voucher-stats'),
        ]
        return self.post_process_urls(urls)


application = VoucherDashboardApplication()
