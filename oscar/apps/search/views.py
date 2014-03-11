from oscar.core.loading import get_model
from haystack import views

from . import facets, signals

Product = get_model('catalogue', 'Product')


class FacetedSearchView(views.FacetedSearchView):
    """
    A modified version of Haystack's FacetedSearchView

    Note that facets are configured when the ``SearchQuerySet`` is initialised.
    This takes place in the search application class.

    See
    http://django-haystack.readthedocs.org/en/v2.1.0/views_and_forms.html#facetedsearchform # noqa
    """

    # Haystack uses a different class attribute to CBVs
    template = "search/results.html"
    search_signal = signals.user_search

    def __call__(self, request):
        response = super(FacetedSearchView, self).__call__(request)

        # Raise a signal for other apps to hook into for analytics
        self.search_signal.send(
            sender=self, session=self.request.session,
            user=self.request.user, query=self.query)

        return response

    # Override this method to add the spelling suggestion to the context and to
    # convert Haystack's default facet data into a more useful structure so we
    # have to do less work in the template.
    def extra_context(self):
        extra = super(FacetedSearchView, self).extra_context()

        # Show suggestion no matter what.  Haystack 2.1 only shows a suggestion
        # if there are some results, which seems a bit weird to me.
        if self.results.query.backend.include_spelling:
            suggestion = self.form.get_suggestion()
            if suggestion != self.query:
                extra['suggestion'] = suggestion

        # Convert facet data into a more useful datastructure
        if 'fields' in extra['facets']:
            extra['facet_data'] = facets.facet_data(
                self.request, self.form, self.results)
            has_facets = any([len(data['results']) for
                              data in extra['facet_data'].values()])
            extra['has_facets'] = has_facets

        # Pass list of selected facets so they can be included in the sorting
        # form.
        extra['selected_facets'] = self.request.GET.getlist('selected_facets')

        return extra

    def get_results(self):
        # We're only interested in products (there might be other content types
        # in the Solr index).
        return super(FacetedSearchView, self).get_results().models(Product)
