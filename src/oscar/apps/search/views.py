# pylint: disable=E1101
from urllib.parse import quote

from django.contrib import messages
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
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
BaseFacetedSearchView = get_class("search.generic_views", "FacetedSearchView")


class BaseSearchView:
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


class FacetedSearchView(BaseSearchView, BaseFacetedSearchView):
    form_class = SearchForm


class BaseCatalogueView:
    context_object_name = "products"
    template_name = "oscar/catalogue/browse.html"
    enforce_paths = True

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # Redirect to page one.
            messages.error(request, _("The given page number was invalid."))
            return redirect("catalogue:index")

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["summary"] = _("All products")
        return ctx


class CatalogueView(BaseCatalogueView, BaseFacetedSearchView):
    """
    Browse all products in the catalogue
    """

    form_class = BrowseSearchForm


class BaseProductCategoryView:
    enforce_paths = True
    context_object_name = "products"
    template_name = "oscar/catalogue/category.html"

    def get(self, request, *args, **kwargs):
        self.category = self.get_category()  # pylint: disable=W0201

        # Allow staff members so they can test layout etc.
        if not self.is_viewable(self.category, request):
            raise Http404()

        potential_redirect = self.redirect_if_necessary(request.path, self.category)
        if potential_redirect is not None:
            return potential_redirect

        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            messages.error(request, _("The given page number was invalid."))
            return redirect(self.category.get_absolute_url())

    def is_viewable(self, category, request):
        return category.is_public or request.user.is_staff

    def redirect_if_necessary(self, current_path, category):
        if self.enforce_paths:
            # Categories are fetched by primary key to allow slug changes.
            # If the slug has changed, issue a redirect.
            expected_path = category.get_absolute_url()
            if expected_path != quote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def get_category(self):
        return get_object_or_404(Category, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ProductCategoryView(BaseProductCategoryView, BaseFacetedSearchView):
    """
    Browse products in a given category
    """

    form_class = CategorySearchForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categories"] = self.category.get_descendants_and_self()
        return kwargs
