from django.conf.urls import url
from django.conf import settings

from haystack.query import SearchQuerySet
from haystack.views import search_view_factory
from oscar.core.application import Application
from oscar.core.loading import get_class


class SearchApplication(Application):
    name = 'search'
    search_view = get_class('search.views', 'FacetedSearchView')
    search_form = get_class('search.forms', 'SearchForm')

    def get_urls(self):

        # The form class has to be passed to the __init__ method as that is how
        # Haystack works.  It's slightly different to normal CBVs.
        urlpatterns = [
            url(r'^$', search_view_factory(
                view_class=self.search_view,
                form_class=self.search_form,
                searchqueryset=self.get_sqs()),
                name='search'),
        ]
        return self.post_process_urls(urlpatterns)

    def get_sqs(self):
        """
        Return the SQS required by a the Haystack search view
        """
        # Build SQS based on the OSCAR_SEARCH_FACETS settings
        sqs = SearchQuerySet()
        for facet in settings.OSCAR_SEARCH_FACETS['fields'].values():
            options = facet.get('options', {})
            sqs = sqs.facet(facet['field'], **options)
        for facet in settings.OSCAR_SEARCH_FACETS['queries'].values():
            for query in facet['queries']:
                sqs = sqs.query_facet(facet['field'], query[1])
        return sqs


application = SearchApplication()
