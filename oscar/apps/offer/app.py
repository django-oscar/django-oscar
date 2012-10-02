from django.conf.urls import patterns, url

from oscar.apps.offer import views
from oscar.core.application import Application


class OfferApplication(Application):
    name = 'offer'
    detail_view = views.OfferDetailView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^(?P<slug>[\w-]+)/$', self.detail_view.as_view(), name='detail'),
        )
        return self.post_process_urls(urlpatterns)


application = OfferApplication()
