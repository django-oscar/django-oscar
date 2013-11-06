from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.orders import views


class OrdersDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]
    permissions_map = {
        'order-list':             (['is_staff'], ['partner.dashboard_access']),
        'order-stats':            (['is_staff'], ['partner.dashboard_access']),
        'order-detail':           (['is_staff'], ['partner.dashboard_access']),
        'order-detail-note':      (['is_staff'], ['partner.dashboard_access']),
        'order-line-detail':      (['is_staff'], ['partner.dashboard_access']),
        'order-shipping-address': (['is_staff'], ['partner.dashboard_access']),
    }

    order_list_view = views.OrderListView
    order_detail_view = views.OrderDetailView
    shipping_address_view = views.ShippingAddressUpdateView
    line_detail_view = views.LineDetailView
    order_stats_view = views.OrderStatsView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.order_list_view.as_view(), name='order-list'),
            url(r'^statistics/$', self.order_stats_view.as_view(), name='order-stats'),
            url(r'^(?P<number>[-\w]+)/$',
                self.order_detail_view.as_view(), name='order-detail'),
            url(r'^(?P<number>[-\w]+)/notes/(?P<note_id>\d+)/$',
                self.order_detail_view.as_view(), name='order-detail-note'),
            url(r'^(?P<number>[-\w]+)/lines/(?P<line_id>\d+)/$',
                self.line_detail_view.as_view(), name='order-line-detail'),
            url(r'^(?P<number>[-\w]+)/shipping-address/$',
                self.shipping_address_view.as_view(), name='order-shipping-address'),
        )
        return self.post_process_urls(urlpatterns)


application = OrdersDashboardApplication()
