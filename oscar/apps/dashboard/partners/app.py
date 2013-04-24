from django.conf.urls import patterns, url

from oscar.views.decorators import staff_member_required
from oscar.core.application import Application
from oscar.apps.dashboard.partners import views


class PartnersDashboardApplication(Application):
    name = None
    list_view = views.PartnerListView
    create_view = views.PartnerCreateView
    update_view = views.PartnerUpdateView
    delete_view = views.PartnerDeleteView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='partner-list'),
            url(r'^create/$', self.create_view.as_view(),
                name='partner-create'),
            url(r'^(?P<pk>\d+)/update/$', self.update_view.as_view(),
                name='partner-update'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(),
                name='partner-delete'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = PartnersDashboardApplication()
