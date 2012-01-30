from django.conf.urls.defaults import patterns, url, include
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.reports.app import application as reports_app
from oscar.apps.dashboard.orders.app import application as orders_app
from oscar.apps.dashboard.users.app import application as users_app
from oscar.apps.dashboard import views


class DashboardApplication(Application):
    name = 'dashboard'
    
    index_view = views.IndexView
    reports_app = reports_app
    orders_app = orders_app
    users_app = users_app

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^reports/', include(self.reports_app.urls)),
            url(r'^orders/', include(self.orders_app.urls)),
            url(r'^users/', include(self.users_app.urls)),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = DashboardApplication()
