from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard import views


class DashboardApplication(Application):
    name = 'dashboard'
    
    index_view = views.IndexView
    orders_view = views.OrderListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^orders/$', self.orders_view.as_view(), name='orders'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = DashboardApplication()
