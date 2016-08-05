from django.conf.urls import url

from oscar.core.application import DashboardApplication
from oscar.core.loading import get_class


class OffersDashboardApplication(DashboardApplication):
    name = None
    default_permissions = ['is_staff', ]

    list_view = get_class('dashboard.offers.views', 'OfferListView')
    metadata_view = get_class('dashboard.offers.views', 'OfferMetaDataView')
    condition_view = get_class('dashboard.offers.views', 'OfferConditionView')
    benefit_view = get_class('dashboard.offers.views', 'OfferBenefitView')
    restrictions_view = get_class('dashboard.offers.views',
                                  'OfferRestrictionsView')
    delete_view = get_class('dashboard.offers.views', 'OfferDeleteView')
    detail_view = get_class('dashboard.offers.views', 'OfferDetailView')

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='offer-list'),
            # Creation
            url(r'^new/name-and-description/$', self.metadata_view.as_view(),
                name='offer-metadata'),
            url(r'^new/condition/$', self.condition_view.as_view(),
                name='offer-condition'),
            url(r'^new/incentive/$', self.benefit_view.as_view(),
                name='offer-benefit'),
            url(r'^new/restrictions/$', self.restrictions_view.as_view(),
                name='offer-restrictions'),
            # Update
            url(r'^(?P<pk>\d+)/name-and-description/$',
                self.metadata_view.as_view(update=True),
                name='offer-metadata'),
            url(r'^(?P<pk>\d+)/condition/$',
                self.condition_view.as_view(update=True),
                name='offer-condition'),
            url(r'^(?P<pk>\d+)/incentive/$',
                self.benefit_view.as_view(update=True),
                name='offer-benefit'),
            url(r'^(?P<pk>\d+)/restrictions/$',
                self.restrictions_view.as_view(update=True),
                name='offer-restrictions'),
            # Delete
            url(r'^(?P<pk>\d+)/delete/$',
                self.delete_view.as_view(), name='offer-delete'),
            # Stats
            url(r'^(?P<pk>\d+)/$', self.detail_view.as_view(),
                name='offer-detail'),
        ]
        return self.post_process_urls(urls)


application = OffersDashboardApplication()
