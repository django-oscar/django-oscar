import warnings
from django.utils.http import urlquote
from django.http import HttpResponsePermanentRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model
from oscar.apps.catalogue.signals import product_viewed

Product = get_model('catalogue', 'product')
Category = get_model('catalogue', 'category')


class ProductDetailView(DetailView):
    context_object_name = 'product'
    model = Product
    view_signal = product_viewed
    template_folder = "catalogue"

    # Whether to redirect to the URL with the right path
    enforce_paths = True

    # Whether to redirect child products to their parent's URL
    enforce_parent = True

    def get(self, request, **kwargs):
        """
        Ensures that the correct URL is used before rendering a response
        """
        self.object = product = self.get_object()

        redirect = self.redirect_if_necessary(request.path, product)
        if redirect is not None:
            return redirect

        response = super(ProductDetailView, self).get(request, **kwargs)
        self.send_signal(request, response, product)
        return response

    def get_object(self, queryset=None):
        # Check if self.object is already set to prevent unnecessary DB calls
        if hasattr(self, 'object'):
            return self.object
        else:
            return super(ProductDetailView, self).get_object(queryset)

    def redirect_if_necessary(self, current_path, product):
        if self.enforce_parent and product.is_child:
            return HttpResponsePermanentRedirect(
                product.parent.get_absolute_url())

        if self.enforce_paths:
            expected_path = product.get_absolute_url()
            if expected_path != urlquote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def send_signal(self, request, response, product):
        self.view_signal.send(
            sender=self, product=product, user=request.user, request=request,
            response=response)

    def get_template_names(self):
        """
        Return a list of possible templates.

        If an overriding class sets a template name, we use that. Otherwise,
        we try 2 options before defaulting to catalogue/detail.html:
            1). detail-for-upc-<upc>.html
            2). detail-for-class-<classname>.html

        This allows alternative templates to be provided for a per-product
        and a per-item-class basis.
        """
        if self.template_name:
            return [self.template_name]

        return [
            '%s/detail-for-upc-%s.html' % (
                self.template_folder, self.object.upc),
            '%s/detail.html' % (self.template_folder)]


class CatalogueView(TemplateView):
    """
    Browse all products in the catalogue
    """
    context_object_name = "products"
    template_name = 'catalogue/browse.html'

    def get_context_data(self, **kwargs):
        ctx = {}
        ctx['summary'] = _("All products")
        return ctx


class ProductCategoryView(TemplateView):
    """
    Browse products in a given category
    """
    context_object_name = "products"
    template_name = 'catalogue/category.html'
    enforce_paths = True

    def get(self, request, *args, **kwargs):
        # Fetch the category; return 404 or redirect as needed
        self.category = self.get_category()
        potential_redirect = self.redirect_if_necessary(
            request.path, self.category)
        if potential_redirect is not None:
            return potential_redirect

        return super(ProductCategoryView, self).get(request, *args, **kwargs)

    def get_category(self):
        if 'pk' in self.kwargs:
            # Usual way to reach a category page. We just look at the primary
            # key, which is easy on the database. If the slug changed, get()
            # will redirect appropriately.
            # WARNING: Category.get_absolute_url needs to look up it's parents
            # to compute the URL. As this is slightly expensive, Oscar's
            # default implementation caches the method. That's pretty safe
            # as ProductCategoryView does the lookup by primary key, which
            # will work even if the cache is stale. But if you override this
            # logic, consider if that still holds true.
            return get_object_or_404(Category, pk=self.kwargs['pk'])
        elif 'category_slug' in self.kwargs:
            # DEPRECATED. TODO: Remove in Oscar 1.2.
            # For SEO and legacy reasons, we allow chopping off the primary
            # key from the URL. In that case, we have the target category slug
            # and it's ancestors' slugs concatenated together.
            # To save on queries, we pick the last slug, look up all matching
            # categories and only then compare.
            # Note that currently we enforce uniqueness of slugs, but as that
            # might feasibly change soon, it makes sense to be forgiving here.
            concatenated_slugs = self.kwargs['category_slug']
            slugs = concatenated_slugs.split(Category._slug_separator)
            try:
                last_slug = slugs[-1]
            except IndexError:
                raise Http404
            else:
                for category in Category.objects.filter(slug=last_slug):
                    if category.full_slug == concatenated_slugs:
                        message = (
                            "Accessing categories without a primary key"
                            " is deprecated will be removed in Oscar 1.2.")
                        warnings.warn(message, DeprecationWarning)

                        return category

        raise Http404

    def redirect_if_necessary(self, current_path, category):
        if self.enforce_paths:
            # Categories are fetched by primary key to allow slug changes.
            # If the slug has changed, issue a redirect.
            expected_path = category.get_absolute_url()
            if expected_path != urlquote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def get_categories(self):
        """
        Return a list of the current category and its ancestors
        """
        return self.category.get_descendants_and_self()

    def get_context_data(self, **kwargs):
        context = super(ProductCategoryView, self).get_context_data(**kwargs)
        context['category'] = self.category
        return context
