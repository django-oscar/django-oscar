from django.conf.urls.defaults import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.reports.app import application as reports_app
from oscar.apps.dashboard import views


class DashboardApplication(Application):
    name = 'dashboard'
    
    index_view = views.IndexView
    order_list_view = views.OrderListView
    order_detail_view = views.OrderDetailView

    reports_app = reports_app

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^reports/', include(self.reports_app.urls)),
            url(r'^orders/$', self.order_list_view.as_view(), name='orders'),
            url(r'^orders/(?P<number>[-\w]+)/$', self.order_detail_view.as_view(), name='order'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = DashboardApplication()
