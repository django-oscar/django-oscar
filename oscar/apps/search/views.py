import json

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View
from django.conf import settings
from django.db.models import get_model
from haystack.query import SearchQuerySet
from haystack.views import FacetedSearchView

Product = get_model('catalogue', 'Product')


class SuggestionsView(View):
    """
    Auto-suggest view

    Return JSON search suggestions for integration with Javascript autocomplete
    plugins.
    """
    suggest_limit = settings.OSCAR_SEARCH_SUGGEST_LIMIT

    def get(self, request):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self):
        """
        Creates a list of suggestions
        """
        query = self.request.GET.get('q', '').strip()
        if not query:
            return self.render_to_response([])

        qs = self.get_search_queryset(query)[:self.suggest_limit]
        context = []
        for item in qs:
            context.append({
                'title': item.object.title,
                'description': item.object.description,
                'url':  item.object.get_absolute_url(),
            })
        return context

    def get_search_queryset(self, query):
        """
        Return the SearchQuerySet for the given query
        """
        return SearchQuerySet().filter(text__contains=query)

    def render_to_response(self, context):
        payload = json.dumps(context)
        return HttpResponse(
            payload, content_type='application/json')


class MultiFacetedSearchView(FacetedSearchView):
    """
    Search view for multifaceted searches
    """
    template = 'search/results.html'

    def __call__(self, request, *args, **kwargs):
        """
        Generates the actual response to the search.

        Relies on internal, overridable methods to construct the response.
        """
        # Look for UPC match
        query = request.GET.get('q', '').strip()
        try:
            item = Product._default_manager.get(upc=query)
            return HttpResponseRedirect(item.get_absolute_url())
        except Product.DoesNotExist:
            pass
        return super(MultiFacetedSearchView, self).__call__(
            request, *args, **kwargs)

    @property
    def __name__(self):
        return "MultiFacetedSearchView"

    def extra_context(self):
        """
        Adds details about the facets applied
        """
        extra = super(MultiFacetedSearchView, self).extra_context()

        if hasattr(self.form, 'cleaned_data') and 'selected_facets' in self.form.cleaned_data:
            extra['facets_applied'] = []
            for f in self.form.cleaned_data['selected_facets'].split("|"):
                facet = f.split(":")
                extra['facets_applied'].append({
                    # removing the _exact suffix that haystack uses for some reason
                    'facet': facet[0][:-6],
                    'value': facet[1].strip('"')
                })
        return extra
