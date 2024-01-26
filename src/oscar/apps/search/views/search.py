from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model
from oscar.apps.search.signals import user_search

SearchForm = get_class("search.forms", "SearchForm")
Product = get_model("catalogue", "product")
Category = get_model("catalogue", "category")
ProductAlert = get_model("customer", "ProductAlert")
ProductAlertForm = get_class("customer.forms", "ProductAlertForm")
BrowseSearchForm = get_class("search.forms", "BrowseSearchForm")
CategorySearchForm = get_class("search.forms", "CategorySearchForm")
BaseSearchView = get_class("search.views.base", "BaseSearchView")


class FacetedSearchView(BaseSearchView):
    form_class = SearchForm
    template_name = "oscar/search/results.html"
    context_object_name = "results"

    def dispatch(self, request, *args, **kwargs):
        # Raise a signal for other apps to hook into for analytics
        user_search.send(
            sender=self,
            session=self.request.session,
            user=self.request.user,
            query=self.request.GET.get("q"),
        )

        return super().dispatch(request, *args, **kwargs)
