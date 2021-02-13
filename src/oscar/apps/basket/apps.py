from django.contrib.auth.decorators import login_required
from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class BasketConfig(OscarConfig):
    label = 'basket'
    name = 'oscar.apps.basket'
    verbose_name = _('Basket')

    namespace = 'basket'

    def ready(self):
        self.summary_view = get_class('basket.views', 'BasketView')
        self.saved_view = get_class('basket.views', 'SavedView')
        self.add_view = get_class('basket.views', 'BasketAddView')

    def get_urls(self):
        urls = [
            path('', self.summary_view.as_view(), name='summary'),
            path('add/<int:pk>/', self.add_view.as_view(), name='add'),
            path('saved/', login_required(self.saved_view.as_view()), name='saved'),
        ]
        return self.post_process_urls(urls)
