from django.http import HttpResponseRedirect
from django.db.models import get_model
from haystack import views

from . import facets

Product = get_model('catalogue', 'Product')


class FacetedSearchView(views.FacetedSearchView):

    def extra_context(self):
        extra = super(FacetedSearchView, self).extra_context()

        if 'fields' in extra['facets']:
            # Convert facet data into a more useful datastructure
            extra['facet_data'] = facets.facet_data(
                self.request, self.form, self.results)

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
        except Product.DoesNotExist:
            pass
        else:
            return HttpResponseRedirect(item.get_absolute_url())
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
                    'value': facet[1].strip('"')
                })
        return extra
