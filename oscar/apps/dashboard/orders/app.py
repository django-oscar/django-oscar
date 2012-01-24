from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.orders import views


class OrdersDashboardApplication(Application):
    name = None
    order_list_view = views.OrderListView
    order_detail_view = views.OrderDetailView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.order_list_view.as_view(), name='order-list'),
            url(r'^(?P<number>[-\w]+)/$',
                self.order_detail_view.as_view(), name='order-detail'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = OrdersDashboardApplication()
