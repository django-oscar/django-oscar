from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class OfferConfig(OscarConfig):
    label = 'offer'
    name = 'oscar.apps.offer'
    verbose_name = _('Offer')

    namespace = 'offer'

    def ready(self):
        from . import receivers  # noqa

        self.detail_view = get_class('offer.views', 'OfferDetailView')
        self.list_view = get_class('offer.views', 'OfferListView')

    def get_urls(self):
        urls = [
            path('', self.list_view.as_view(), name='list'),
            path('<slug:slug>/', self.detail_view.as_view(), name='detail'),
        ]
        return self.post_process_urls(urls)
