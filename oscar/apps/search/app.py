from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.search import views, forms
from haystack.views import search_view_factory
from haystack.query import SearchQuerySet


class SearchApplication(Application):
    name = 'search'
    search_view = views.MultiFacetedSearchView

    def get_urls(self):
        # Set the fields to facet on
        sqs = (SearchQuerySet().facet('price')
                               .facet('num_in_stock')
                               .facet('category')
                               .query_facet('price_exact', '[0 TO 20]')
                               .query_facet('price_exact', '[20 TO 40]')
                               .query_facet('price_exact', '[40 TO 60]'))

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
                name='search_default'),
        )
        return self.post_process_urls(urlpatterns)


application = SearchApplication()
