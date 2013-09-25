from django.conf.urls import patterns, url
from django.conf import settings

from oscar.core.application import Application
from oscar.apps.search import views, forms
from haystack.views import search_view_factory
from haystack.query import SearchQuerySet


class SearchApplication(Application):
    name = 'search'
    search_view = views.MultiFacetedSearchView

    def get_urls(self):
        # Build SQS
        sqs = SearchQuerySet()
        for facet in settings.OSCAR_SEARCH_FACETS['fields'].values():
            sqs = sqs.facet(facet['field'])
        for facet in settings.OSCAR_SEARCH_FACETS['queries'].values():
            for query in facet['queries']:
                sqs = sqs.query_facet(facet['field'], query[1])

        # The form class has to be passed to the __init__ method as that is how
        # Haystack works.  It's slightly different to normal CBVs.
        urlpatterns = patterns('',
            url(r'^$', self.search_view(form_class=forms.MultiFacetedSearchForm),
                name='search'),
            url(r'^default/$', search_view_factory(
                view_class=views.FacetedSearchView,
                form_class=forms.PriceRangeSearchForm,
                searchqueryset=sqs,
                template='search/results.html'),
                name='search-default'),
        )
        return self.post_process_urls(urlpatterns)


application = SearchApplication()
