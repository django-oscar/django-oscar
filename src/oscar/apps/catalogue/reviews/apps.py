from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CatalogueReviewsConfig(OscarConfig):
    label = 'reviews'
    name = 'oscar.apps.catalogue.reviews'
    verbose_name = _('Catalogue reviews')

    hidable_feature_name = 'reviews'

    def ready(self):
        self.detail_view = get_class('catalogue.reviews.views', 'ProductReviewDetail')
        self.create_view = get_class('catalogue.reviews.views', 'CreateProductReview')
        self.vote_view = get_class('catalogue.reviews.views', 'AddVoteView')
        self.list_view = get_class('catalogue.reviews.views', 'ProductReviewList')

    def get_urls(self):
        urls = [
            url(r'^(?P<pk>\d+)/$', self.detail_view.as_view(),
                name='reviews-detail'),
            url(r'^add/$', self.create_view.as_view(),
                name='reviews-add'),
            url(r'^(?P<pk>\d+)/vote/$',
                login_required(self.vote_view.as_view()),
                name='reviews-vote'),
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
        ]
        return self.post_process_urls(urls)
