from django.conf.urls.defaults import *
from haystack.query import SearchQuerySet
from oscar.search.views import Suggestions, MultiFacetedSearchView
from oscar.search.forms import MultiFacetedSearchForm

sqs = SearchQuerySet()

urlpatterns = patterns('search.views',
    url(r'^suggest/$', Suggestions.as_view(), name='search.suggest'),
    url(r'^$', MultiFacetedSearchView(form_class=MultiFacetedSearchForm, searchqueryset=sqs), name='search.results'),
)