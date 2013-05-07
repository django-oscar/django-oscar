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

    manage_users_view = views.PartnerManageUsers
    unlink_user_view = views.PartnerUnlinkUserView
    create_user_view = views.PartnerCreateUserView

    update_user_view = views.PartnerUpdateUserView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='partner-list'),
            url(r'^create/$', self.create_view.as_view(),
                name='partner-create'),
            url(r'^(?P<pk>\d+)/update/$', self.update_view.as_view(),
                name='partner-update'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(),
                name='partner-delete'),

            url(r'^(?P<pk>\d+)/users/$',
                self.manage_users_view.as_view(),
                name='partner-user-list'),
            url(r'^(?P<partner_pk>\d+)/users/add/$',
                self.create_user_view.as_view(),
                name='partner-user-create'),
            url(r'^(?P<partner_pk>\d+)/users/(?P<user_pk>\d+)/unlink/$',
                self.unlink_user_view.as_view(), name='partner-user-unlink'),

            url(r'^users/(?P<pk>\d+)/update/$',
                self.update_user_view.as_view(),
                name='partner-user-update'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = PartnersDashboardApplication()
