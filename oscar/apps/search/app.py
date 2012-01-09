from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from haystack.query import SearchQuerySet

from oscar.core.application import Application
from oscar.apps.search.views import SuggestionsView, MultiFacetedSearchView
from oscar.apps.search.search_indexes import ProductIndex
from oscar.apps.search.forms import MultiFacetedSearchForm


class SearchApplication(Application):
    name = 'search'
    
    suggestions_view = SuggestionsView
    search_view = MultiFacetedSearchView

    def get_urls(self):
        sqs = SearchQuerySet()
        for field_name, field in ProductIndex.fields.items():
            if field.faceted is True:
                # Ensure we facet the results set by the defined facetable fields
                sqs.facet(field_name)
        
        urlpatterns = patterns('',
            url(r'^suggest/$', self.suggestions_view.as_view(), name='suggest'),
            url(r'^$', self.search_view(form_class=MultiFacetedSearchForm, 
                                        searchqueryset=sqs), name='search'),
        )
        return self.post_process_urls(urlpatterns)


application = SearchApplication()