from django.conf.urls.defaults import *
from haystack.query import SearchQuerySet

from oscar.apps.search.views import Suggestions, MultiFacetedSearchView
from oscar.apps.search.forms import MultiFacetedSearchForm
from oscar.apps.search.search_indexes import ProductIndex

sqs = SearchQuerySet()
for field_name, field in ProductIndex.fields.items():
    if field.faceted is True:
        #ensure we facet the results set by the defined facetable fields
        sqs.facet(field_name)

urlpatterns = patterns('search.views',
    url(r'^suggest/$', Suggestions.as_view(), name='oscar-search-suggest'),
    url(r'^$', MultiFacetedSearchView(form_class=MultiFacetedSearchForm, searchqueryset=sqs), name='oscar-search'),
)