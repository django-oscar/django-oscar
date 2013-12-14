from django.conf.urls import patterns, url

from oscar.apps.offer import views
from oscar.core.application import Application


class OfferApplication(Application):
    name = 'offer'
    detail_view = views.OfferDetailView
    list_view = views.OfferListView

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='list'),
            url(r'^(?P<slug>[\w-]+)/$', self.detail_view.as_view(),
                name='detail'),
        ]
        return self.post_process_urls(patterns('', *urls))


application = OfferApplication()
