from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.pages import views


class FlatPageManagementApplication(Application):
    name = None
    list_view = views.PageListView
    create_view = views.PageCreateView
    update_view = views.PageUpdateView
    delete_view = views.PageDeleteView

    def get_urls(self):
        """
        Get URL patterns defined for flatpage management application.
        """
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='page-list'),
            url(r'^create/$', self.create_view.as_view(), name='page-create'),
            url(r'^update/(?P<pk>[-\w]+)/$',
                self.update_view.as_view(), name='page-update'),
            url(r'^delete/(?P<pk>\d+)/$',
                self.delete_view.as_view(), name='page-delete')
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = FlatPageManagementApplication()
