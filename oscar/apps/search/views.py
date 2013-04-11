import json

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View
from django.conf import settings
from django.db.models import get_model
from haystack.query import SearchQuerySet
from haystack import views
from purl import URL

Product = get_model('catalogue', 'Product')


class SuggestionsView(View):
    """
    Auto suggest view

    Returns the suggestions in JSON format (especially suited for consumption
    by jQuery autocomplete) """

    suggest_limit = settings.OSCAR_SEARCH_SUGGEST_LIMIT

    def get(self, request):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self):
        '''
        Creates a list of suggestions
        '''
        query_term = self.request.GET['query_term']
        query_set = SearchQuerySet().filter(text__contains=query_term)[
            :self.suggest_limit]
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


class FacetedSearchView(views.FacetedSearchView):

    def extra_context(self):
        extra = super(FacetedSearchView, self).extra_context()

        # Convert facet data into a more useful datastructure

        # Field facets
        facet_data = {}
        base_url = URL(self.request.get_full_path())
        selected = dict(
            map(lambda x: x.split(':'), self.form.selected_facets))
        for field, facets in extra['facets']['fields'].items():
            facet_data[field] = []
            for name, count in facets:
                # Ignore zero-count facets for field
                if count == 0:
                    continue
                field_filter = '%s_exact' % field
                datum = {
                    'name': name,
                    'count': count}
                if selected.get(field_filter, None) == name:
                    # This filter is selected - build the 'deselect' URL
                    datum['selected'] = True
                    url = base_url.remove_query_param(
                        'selected_facets', '%s:%s' % (
                            field_filter, name))
                    datum['deselect_url'] = url.as_string()
                else:
                    # This filter is not selected - built the 'select' URL
                    datum['selected'] = False
                    url = base_url.append_query_param(
                        'selected_facets', '%s:%s' % (
                            field_filter, name))
                    datum['select_url'] = url.as_string()
                facet_data[field].append(datum)

        # Query facets
        for key, facet in settings.OSCAR_SEARCH_FACETS['queries'].items():
            facet_data[key] = []
            for name, query in facet['queries']:
                field_filter = '%s_exact' % facet['field']
                match = '%s_exact:%s' % (facet['field'], query)
                if not match in extra['facets']['queries']:
                    datum = {
                        'name': name,
                        'count': 0,
                    }
                else:
                    datum = {
                        'name': name,
                        'count': extra['facets']['queries'][match],
                    }
                    if selected.get(field_filter, None) == query:
                        # Selected
                        datum['selected'] = True
                        url = base_url.remove_query_param(
                            'selected_facets', match)
                        datum['deselect_url'] = url.as_string()
                    else:
                        datum['selected'] = False
                        url = base_url.append_query_param(
                            'selected_facets', match)
                        datum['select_url'] = url.as_string()
                    facet_data[key].append(datum)

        extra['facet_data'] = facet_data

        return extra


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
        return super(MultiFacetedSearchView, self).__call__(request, *args, **kwargs)

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
                    'facet': facet[0][:-6], # removing the _exact suffix that haystack uses for some reason
                    'value' : facet[1].strip('"')
                })
        return extra
