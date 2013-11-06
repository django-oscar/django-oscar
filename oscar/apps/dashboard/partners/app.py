from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.partners import views


class PartnersDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    list_view = views.PartnerListView
    create_view = views.PartnerCreateView
    manage_view = views.PartnerManageView
    delete_view = views.PartnerDeleteView

    user_link_view = views.PartnerUserLinkView
    user_unlink_view = views.PartnerUserUnlinkView
    user_create_view = views.PartnerUserCreateView
    user_select_view = views.PartnerUserSelectView
    user_update_view = views.PartnerUserUpdateView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='partner-list'),
            url(r'^create/$', self.create_view.as_view(),
                name='partner-create'),
            url(r'^(?P<pk>\d+)/$', self.manage_view.as_view(),
                name='partner-manage'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(),
                name='partner-delete'),

            url(r'^(?P<partner_pk>\d+)/users/add/$',
                self.user_create_view.as_view(),
                name='partner-user-create'),
            url(r'^(?P<partner_pk>\d+)/users/select/$',
                self.user_select_view.as_view(),
                name='partner-user-select'),
            url(r'^(?P<partner_pk>\d+)/users/(?P<user_pk>\d+)/link/$',
                self.user_link_view.as_view(), name='partner-user-link'),
            url(r'^(?P<partner_pk>\d+)/users/(?P<user_pk>\d+)/unlink/$',
                self.user_unlink_view.as_view(), name='partner-user-unlink'),
            url(r'^(?P<partner_pk>\d+)/users/(?P<user_pk>\d+)/update/$',
                self.user_update_view.as_view(),
                name='partner-user-update'),
        )
        return self.post_process_urls(urlpatterns)


application = PartnersDashboardApplication()
