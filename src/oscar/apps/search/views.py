from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView

from oscar.core.loading import get_class
from oscar.apps.search.signals import user_search

SearchForm = get_class("search.forms", "SearchForm")
BaseFacetedSearchView = get_class("search.generic_views", "FacetedSearchView")


class FacetedSearchView(BaseFacetedSearchView):
    template_name = "oscar/search/results.html"
    context_object_name = "results"
    form_class = SearchForm

    def dispatch(self, request, *args, **kwargs):
        # Raise a signal for other apps to hook into for analytics
        user_search.send(
            sender=self,
            session=self.request.session,
            user=self.request.user,
            query=self.request.GET.get("q"),
        )

        return super().dispatch(request, *args, **kwargs)
