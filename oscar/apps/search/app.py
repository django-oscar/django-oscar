from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.search.views import MultiFacetedSearchView
from oscar.apps.search.forms import MultiFacetedSearchForm


class SearchApplication(Application):
    name = 'search'
    search_view = MultiFacetedSearchView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.search_view(form_class=MultiFacetedSearchForm), name='search'),
        )
        return self.post_process_urls(urlpatterns)


application = SearchApplication()