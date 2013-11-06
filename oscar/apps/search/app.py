from django.conf.urls import patterns, url
from django.conf import settings

from haystack.query import SearchQuerySet
from haystack.views import search_view_factory
from oscar.apps.search import views, forms
from oscar.core.application import Application


class SearchApplication(Application):
    name = 'search'
    search_view = views.MultiFacetedSearchView

    def get_urls(self):
        # Build SQS based on the OSCAR_SEARCH_FACETS settings
        sqs = SearchQuerySet()
        for facet in settings.OSCAR_SEARCH_FACETS['fields'].values():
            sqs = sqs.facet(facet['field'])
        for facet in settings.OSCAR_SEARCH_FACETS['queries'].values():
            for query in facet['queries']:
                sqs = sqs.query_facet(facet['field'], query[1])

        # The form class has to be passed to the __init__ method as that is how
        # Haystack works.  It's slightly different to normal CBVs.
        urlpatterns = patterns(
            '',
            # This view is used in the default templates (at the moment)
            url(r'^$', self.search_view(
                form_class=forms.MultiFacetedSearchForm),
                name='search'),
            # This view is used in the demo site.
            url(r'^default/$', search_view_factory(
                view_class=views.FacetedSearchView,
                form_class=forms.PriceRangeSearchForm,
                searchqueryset=sqs,
                template='search/results.html'),
                name='search-default'),
        )
        return self.post_process_urls(urlpatterns)


application = SearchApplication()
