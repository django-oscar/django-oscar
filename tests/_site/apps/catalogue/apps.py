from django.conf.urls import url

from oscar.apps.catalogue import apps


class CatalogueConfig(apps.CatalogueConfig):
    name = 'tests._site.apps.catalogue'

    def get_urls(self):
        from .views import ParentProductDetailView

        urls = super().get_urls()
        urls += [
            url(r'^parent/(?P<product_slug>[\w-]*)_(?P<pk>\d+)/$', ParentProductDetailView.as_view(),
                name='parent_detail')
        ]
        return self.post_process_urls(urls)
