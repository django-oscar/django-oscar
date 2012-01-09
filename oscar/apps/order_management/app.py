from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.order_management.views import OrderListView, OrderDetailView


class OrderManagementApplication(Application):
    name = 'order-management'
    
    list_view = OrderListView
    detail_view = OrderDetailView

    def get_urls(self):
        urlpatterns = patterns('oscar.order_management.views',
            url(r'^$', staff_member_required(self.list_view.as_view()), name='list'),
            url(r'^order/(?P<order_number>[\w-]*)/$', staff_member_required(self.detail_view.as_view()), name='detail'),
        )
        return self.post_process_urls(urlpatterns)


application = OrderManagementApplication()