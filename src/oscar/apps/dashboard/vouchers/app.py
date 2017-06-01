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

    set_list_view = get_class(
        'dashboard.vouchers.views', 'VoucherSetListView')
    set_create_view = get_class(
        'dashboard.vouchers.views', 'VoucherSetCreateView')
    set_update_view = get_class(
        'dashboard.vouchers.views', 'VoucherSetUpdateView')
    set_detail_view = get_class(
        'dashboard.vouchers.views', 'VoucherSetDetailView')
    set_download_view = get_class(
        'dashboard.vouchers.views', 'VoucherSetDownloadView')

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
            url(r'^sets$', self.set_list_view.as_view(),
                name='voucher-set-list'),
            url(r'^sets/create/$', self.set_create_view.as_view(),
                name='voucher-set-create'),
            url(r'^sets/update/(?P<pk>\d+)/$', self.set_update_view.as_view(),
                name='voucher-set-update'),
            url(r'^sets/(?P<pk>\d+)/$', self.set_detail_view.as_view(),
                name='voucher-set'),
            url(r'^sets/(?P<pk>\d+)/download$', self.set_download_view.as_view(),
                name='voucher-set-download'),
        ]
        return self.post_process_urls(urls)


application = VoucherDashboardApplication()
