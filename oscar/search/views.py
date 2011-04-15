from haystack.query import SearchQuerySet
from django.http import HttpResponse
from django.views.generic.base import View
from haystack.views import FacetedSearchView
import json
import settings

class Suggestions(View):
    u"""
    Auto suggest view

    Returns the suggestions in JSON format (especially suited for consumption by
    jQuery autocomplete)
    """

    suggest_limit = getattr(settings, 'OSCAR_SEARCH_SUGGEST_LIMIT', 10)

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

    def __name__(self):
        return "MultiFacetedSearchView"

    def extra_context(self):
        '''
        Adds details about the facets applied
        '''
        extra = super(MultiFacetedSearchView, self).extra_context()

        if hasattr(self.form, 'cleaned_data') and self.form.cleaned_data['selected_facets']:
            extra['facets_applied'] = []
            for f in self.form.cleaned_data['selected_facets'].split("|"):
                facet = f.split(":")
                extra['facets_applied'].append({
                    'facet': facet[0][:-6], # removing the _exact suffix that haystack uses for some reason
                    'value' : facet[1].strip('"')
                })
        return extra