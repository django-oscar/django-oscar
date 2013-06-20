from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.views.decorators import staff_member_required
from oscar.apps.dashboard.users import views


class UserManagementApplication(Application):
    name = None
    index_view = views.IndexView
    user_detail_view = views.UserDetailView
    alert_list_view = views.ProductAlertListView
    alert_update_view = views.ProductAlertUpdateView
    alert_delete_view = views.ProductAlertDeleteView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='users-index'),
            url(r'^(?P<pk>\w+)/$',
                self.user_detail_view.as_view(), name='user-detail'),

            # Alerts
            url(r'^alerts/(?P<pk>\d+)/delete/$',
                self.alert_delete_view.as_view(),
                name='user-alert-delete'),
            url(r'^alerts/(?P<pk>\d+)/update/$',
                self.alert_update_view.as_view(),
                name='user-alert-update'),
            url(r'^alerts/$',
                self.alert_list_view.as_view(),
                name='user-alert-list'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = UserManagementApplication()
