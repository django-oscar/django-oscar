from django.db.models import get_model
from haystack import views

from . import facets

Product = get_model('catalogue', 'Product')


class FacetedSearchView(views.FacetedSearchView):
    # Haystack uses a different class attribute to CBVs
    template = "search/results.html"

    def extra_context(self):
        extra = super(FacetedSearchView, self).extra_context()

        # Show suggestion no matter what.  Haystack 2.1 only shows a suggestion
        # if there are some results, which seems a bit weird to me
        if self.results.query.backend.include_spelling:
            suggestion = self.form.get_suggestion()
            if suggestion != self.query:
                extra['suggestion'] = suggestion

        if 'fields' in extra['facets']:
            # Convert facet data into a more useful datastructure
            extra['facet_data'] = facets.facet_data(
                self.request, self.form, self.results)
            has_facets = any([len(data['results']) for
                              data in extra['facet_data'].values()])
            extra['has_facets'] = has_facets

        return extra
