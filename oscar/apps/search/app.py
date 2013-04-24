from django.conf.urls import patterns, url

from oscar.core.application import Application
from . import views


class SearchApplication(Application):
    name = 'search'
    search_view = views.MultiFacetedSearchView
    suggestions_view = views.SuggestionsView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.search_view(), name='search'),
            url(r'^suggest/$', self.suggestions_view.as_view(),
                name='suggest'),
        )
        return self.post_process_urls(urlpatterns)


application = SearchApplication()
