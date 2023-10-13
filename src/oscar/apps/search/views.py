from django.conf import settings

from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView

from oscar.apps.search.signals import user_search
from oscar.core.loading import get_class, get_model

SearchForm = get_class("search.forms", "SearchForm")
BaseFacetedSearchView = get_class("search.generic_views", "FacetedSearchView")


class FacetedSearchView(BaseFacetedSearchView):
    template_name = "oscar/search/results.html"
    context_object_name = "results"
    form_class = SearchForm
