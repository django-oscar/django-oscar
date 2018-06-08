from django.conf.urls import url

from oscar.core.application import Application as BaseApplication
from oscar.core.loading import get_class

CatalogueSearchView = get_class('catalogue.views', 'CatalogueSearchView')


class Application(BaseApplication):
    name = 'es_search'

    def get_urls(self):
        urls = [
            url(r'^$', CatalogueSearchView.as_view(), name='search'),
        ]
        return self.post_process_urls(urls)


application = Application()
