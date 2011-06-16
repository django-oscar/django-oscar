from django.conf.urls.defaults import *
from haystack.query import SearchQuerySet

from oscar.core.loading import import_module
import_module('search.views', ['Suggestions', 'MultiFacetedSearchView'], locals())
import_module('search.forms', ['MultiFacetedSearchForm'], locals())
import_module('search.search_indexes', ['ProductIndex'], locals())


sqs = SearchQuerySet()
for field_name, field in ProductIndex.fields.items():
    if field.faceted is True:
        # Ensure we facet the results set by the defined facetable fields
        sqs.facet(field_name)

urlpatterns = patterns('search.apps.views',
    url(r'^suggest/$', Suggestions.as_view(), name='oscar-search-suggest'),
    url(r'^$', MultiFacetedSearchView(form_class=MultiFacetedSearchForm, 
                                      searchqueryset=sqs), name='oscar-search'),
)