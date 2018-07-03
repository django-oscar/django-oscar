from django.conf.urls import url
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class, get_model


class PromotionsConfig(OscarConfig):
    label = 'promotions'
    name = 'oscar.apps.promotions'
    verbose_name = _('Promotions')

    namespace = 'promotions'

    def ready(self):
        self.KeywordPromotion = get_model('promotions', 'KeywordPromotion')
        self.PagePromotion = get_model('promotions', 'PagePromotion')

        self.home_view = get_class('promotions.views', 'HomeView')
        self.record_click_view = get_class('promotions.views', 'RecordClickView')

    def get_urls(self):
        urls = [
            url(r'page-redirect/(?P<page_promotion_id>\d+)/$',
                self.record_click_view.as_view(model=self.PagePromotion),
                name='page-click'),
            url(r'keyword-redirect/(?P<keyword_promotion_id>\d+)/$',
                self.record_click_view.as_view(model=self.KeywordPromotion),
                name='keyword-click'),
            url(r'^$', self.home_view.as_view(), name='home'),
        ]
        return self.post_process_urls(urls)
