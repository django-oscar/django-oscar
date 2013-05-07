from django.conf.urls import patterns, url
from oscar.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.offers import views


class OffersDashboardApplication(Application):
    name = None
    list_view = views.OfferListView

    metadata_view = views.OfferMetaDataView
    condition_view = views.OfferConditionView
    benefit_view = views.OfferBenefitView
    restrictions_view = views.OfferRestrictionsView
    delete_view = views.OfferDeleteView
    detail_view = views.OfferDetailView

    def get_urls(self):
        urlpatterns = patterns('',
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
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = OffersDashboardApplication()
