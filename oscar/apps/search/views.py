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
