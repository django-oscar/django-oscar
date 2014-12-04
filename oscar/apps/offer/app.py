from django.conf.urls import url

from oscar.core.application import Application
from oscar.core.loading import get_class


class OfferApplication(Application):
    name = 'offer'
    detail_view = get_class('offer.views', 'OfferDetailView')
    list_view = get_class('offer.views', 'OfferListView')

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='list'),
            url(r'^(?P<slug>[\w-]+)/$', self.detail_view.as_view(),
                name='detail'),
        ]
        return self.post_process_urls(urls)


application = OfferApplication()
