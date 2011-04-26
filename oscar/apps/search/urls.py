from django.conf.urls.defaults import *
from haystack.query import SearchQuerySet

from oscar.core.loading import import_module
search_views = import_module('search.views', ['Suggestions', 'MultiFacetedSearchView'])
search_forms = import_module('search.forms', ['MultiFacetedSearchForm'])
search_indexes = import_module('search.search_indexes', ['ProductIndex'])


sqs = SearchQuerySet()
for field_name, field in search_indexes.ProductIndex.fields.items():
    if field.faceted is True:
        # Ensure we facet the results set by the defined facetable fields
        sqs.facet(field_name)

urlpatterns = patterns('search.apps.views',
    url(r'^suggest/$', search_views.Suggestions.as_view(), name='oscar-search-suggest'),
    url(r'^$', search_views.MultiFacetedSearchView(form_class=search_forms.MultiFacetedSearchForm, 
        searchqueryset=sqs), name='oscar-search'),
)