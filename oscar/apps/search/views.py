import json

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View
from django.conf import settings
from django.template.response import TemplateResponse
from haystack.query import SearchQuerySet
from haystack.views import FacetedSearchView

from oscar.core.loading import import_module
product_models = import_module('catalogue.models', ['Product'])


class SuggestionsView(View):
    u"""
    Auto suggest view

    Returns the suggestions in JSON format (especially suited for consumption by
    jQuery autocomplete)
    """

    suggest_limit = settings.OSCAR_SEARCH_SUGGEST_LIMIT

    def get(self, request):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self):
        '''
        Creates a list of suggestions
        '''
        query_term = self.request.GET['query_term'];
        query_set = SearchQuerySet().filter(text__contains=query_term)[:self.suggest_limit]
        context = []
        for item in query_set:
            context.append({
                'label': item.object.title,
                'url':  item.object.get_absolute_url(),
            })
        return context

    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return HttpResponse(content,
                            content_type='application/json',
                            **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context into a JSON object"
        return json.dumps(context)


class MultiFacetedSearchView(FacetedSearchView):
    u"""
    Search view for multifaceted searches
    """
    template = 'search/results.html'

    def __call__(self, request, *args, **kwargs):
        """
        Generates the actual response to the search.
        
        Relies on internal, overridable methods to construct the response.
        """
        
        # Look for UPC match
        query = request.GET['q'].strip()
        try:
            item = product_models.Product._default_manager.get(upc=query)
            return HttpResponseRedirect(item.get_absolute_url())
        except product_models.Product.DoesNotExist:
            pass
        
        return super(MultiFacetedSearchView, self).__call__(request, *args, **kwargs)

    def __name__(self):
        return "MultiFacetedSearchView"

    def extra_context(self):
        '''
        Adds details about the facets applied
        '''
        extra = super(MultiFacetedSearchView, self).extra_context()

        if hasattr(self.form, 'cleaned_data') and 'selected_facets' in self.form.cleaned_data:
            extra['facets_applied'] = []
            for f in self.form.cleaned_data['selected_facets'].split("|"):
                facet = f.split(":")
                extra['facets_applied'].append({
                    'facet': facet[0][:-6], # removing the _exact suffix that haystack uses for some reason
                    'value' : facet[1].strip('"')
                })
        return extra