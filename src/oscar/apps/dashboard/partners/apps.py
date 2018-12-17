from django.conf.urls import url
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PartnersDashboardConfig(OscarDashboardConfig):
    label = 'partners_dashboard'
    name = 'oscar.apps.dashboard.partners'
    verbose_name = _('Partners dashboard')

    default_permissions = ['is_staff', ]

    def ready(self):
        self.list_view = get_class('dashboard.partners.views', 'PartnerListView')
        self.create_view = get_class('dashboard.partners.views', 'PartnerCreateView')
        self.manage_view = get_class('dashboard.partners.views', 'PartnerManageView')
        self.delete_view = get_class('dashboard.partners.views', 'PartnerDeleteView')

        self.user_link_view = get_class('dashboard.partners.views',
                                        'PartnerUserLinkView')
        self.user_unlink_view = get_class('dashboard.partners.views',
                                          'PartnerUserUnlinkView')
        self.user_create_view = get_class('dashboard.partners.views',
                                          'PartnerUserCreateView')
        self.user_select_view = get_class('dashboard.partners.views',
                                          'PartnerUserSelectView')
        self.user_update_view = get_class('dashboard.partners.views',
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
