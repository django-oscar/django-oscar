from django.conf.urls import url

from oscar.core.application import DashboardApplication
from oscar.core.loading import get_class


class PartnersDashboardApplication(DashboardApplication):
    name = None
    default_permissions = ['is_staff', ]

    list_view = get_class('dashboard.partners.views', 'PartnerListView')
    create_view = get_class('dashboard.partners.views', 'PartnerCreateView')
    manage_view = get_class('dashboard.partners.views', 'PartnerManageView')
    delete_view = get_class('dashboard.partners.views', 'PartnerDeleteView')

    user_link_view = get_class('dashboard.partners.views',
                               'PartnerUserLinkView')
    user_unlink_view = get_class('dashboard.partners.views',
                                 'PartnerUserUnlinkView')
    user_create_view = get_class('dashboard.partners.views',
                                 'PartnerUserCreateView')
    user_select_view = get_class('dashboard.partners.views',
                                 'PartnerUserSelectView')
    user_update_view = get_class('dashboard.partners.views',
                                 'PartnerUserUpdateView')

    def get_urls(self):
        urls = [
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
        ]
        return self.post_process_urls(urls)


application = PartnersDashboardApplication()
