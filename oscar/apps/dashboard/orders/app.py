from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import Application
from oscar.apps.dashboard.orders import views
from oscar.apps.dashboard.nav import register, Node

node = Node(_('Orders'))
node.add_child(Node(_('Orders'), 'dashboard:order-list'))
node.add_child(Node(_('Statistics'), 'dashboard:order-stats'))
register(node, 80)


class OrdersDashboardApplication(Application):
    name = None
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

    def get_url_decorator(self, url_name):
        return staff_member_required


application = OrdersDashboardApplication()
