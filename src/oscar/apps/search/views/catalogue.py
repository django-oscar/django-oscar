# pylint: disable=E1101
from urllib.parse import quote

from django.contrib import messages
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

BrowseCategoryForm = get_class("search.forms", "BrowseCategoryForm")
CategoryForm = get_class("search.forms", "CategoryForm")
BaseSearchView = get_class("search.views.base", "BaseSearchView")
Category = get_model("catalogue", "Category")


class CatalogueView(BaseSearchView):
    """
    Browse all products in the catalogue
    """

    form_class = BrowseCategoryForm
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


class ProductCategoryView(BaseSearchView):
    """
    Browse products in a given category
    """

    form_class = CategoryForm
    enforce_paths = True
    context_object_name = "products"
    template_name = "oscar/catalogue/category.html"

    def get(self, request, *args, **kwargs):
        # pylint: disable=W0201
        self.category = self.get_category()

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categories"] = self.category.get_descendants_and_self()
        return kwargs
