from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CatalogueOnlyConfig(OscarConfig):
    label = 'catalogue'
    name = 'oscar.apps.catalogue'
    verbose_name = _('Catalogue')

    namespace = 'catalogue'

    def ready(self):
        from . import receivers  # noqa

        super().ready()

        self.detail_view = get_class('catalogue.views', 'ProductDetailView')
        self.catalogue_view = get_class('catalogue.views', 'CatalogueView')
        self.category_view = get_class('catalogue.views', 'ProductCategoryView')
        self.range_view = get_class('offer.views', 'RangeDetailView')

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('', self.catalogue_view.as_view(), name='index'),
            re_path(
                r'^(?P<product_slug>[\w-]*)_(?P<pk>\d+)/$',
                self.detail_view.as_view(), name='detail'),
            re_path(
                r'^category/(?P<category_slug>[\w-]+(/[\w-]+)*)_(?P<pk>\d+)/$',
                self.category_view.as_view(), name='category'),
            path('ranges/<slug:slug>/', self.range_view.as_view(), name='range'),
        ]
        return self.post_process_urls(urls)


class CatalogueReviewsOnlyConfig(OscarConfig):
    label = 'catalogue'
    name = 'oscar.apps.catalogue'
    verbose_name = _('Catalogue')

    def get_app_label_url_endpoint_mapping(self):
        return {"reviews": {"endpoint": r"^(?P<product_slug>[\w-]*)_(?P<product_pk>\d+)/reviews/", "regex": True}}

    def ready(self):
        from . import receivers  # noqa

        super().ready()

    def get_urls(self):
        urls = super().get_urls() + self.get_auto_loaded_urls()
        return self.post_process_urls(urls)


class CatalogueConfig(CatalogueOnlyConfig, CatalogueReviewsOnlyConfig):
    """
    Composite class combining Products with Reviews
    """
