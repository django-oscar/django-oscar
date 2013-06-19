from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.vouchers import views


class VoucherDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    list_view = views.VoucherListView
    create_view = views.VoucherCreateView
    update_view = views.VoucherUpdateView
    delete_view = views.VoucherDeleteView
    stats_view = views.VoucherStatsView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='voucher-list'),
            url(r'^create/$', self.create_view.as_view(),
                name='voucher-create'),
            url(r'^update/(?P<pk>\d+)/$', self.update_view.as_view(),
                name='voucher-update'),
            url(r'^delete/(?P<pk>\d+)/$', self.delete_view.as_view(),
                name='voucher-delete'),
            url(r'^stats/(?P<pk>\d+)/$', self.stats_view.as_view(),
                name='voucher-stats'),
        )
        return self.post_process_urls(urlpatterns)


application = VoucherDashboardApplication()
