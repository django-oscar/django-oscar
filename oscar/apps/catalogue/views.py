import warnings
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from oscar.core.loading import get_model
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class
from oscar.apps.catalogue.signals import product_viewed, product_search

Product = get_model('catalogue', 'product')
ProductReview = get_model('reviews', 'ProductReview')
Category = get_model('catalogue', 'category')
ProductAlert = get_model('customer', 'ProductAlert')
ProductAlertForm = get_class('customer.forms', 'ProductAlertForm')


class ProductDetailView(DetailView):
    context_object_name = 'product'
    model = Product
    view_signal = product_viewed
    template_folder = "catalogue"
    enforce_paths = True

    def get(self, request, **kwargs):
        """
        Ensures that the correct URL is used before rendering a response
        """
        self.object = product = self.get_object()

        if self.enforce_paths:
            if product.is_variant:
                return HttpResponsePermanentRedirect(
                    product.parent.get_absolute_url())

            correct_path = product.get_absolute_url()
            if correct_path != request.path:
                return HttpResponsePermanentRedirect(correct_path)

        response = super(ProductDetailView, self).get(request, **kwargs)
        self.send_signal(request, response, product)
        return response

    def get_object(self, queryset=None):
        # Check if self.object is already set to prevent unnecessary DB calls
        if hasattr(self, 'object'):
            return self.object
        else:
            return super(ProductDetailView, self).get_object(queryset)

    def get_context_data(self, **kwargs):
        ctx = super(ProductDetailView, self).get_context_data(**kwargs)
        ctx['reviews'] = self.get_reviews()
        ctx['alert_form'] = self.get_alert_form()
        ctx['has_active_alert'] = self.get_alert_status()

        return ctx

    def get_alert_status(self):
        # Check if this user already have an alert for this product
        has_alert = False
        if self.request.user.is_authenticated():
            alerts = ProductAlert.objects.filter(
                product=self.object, user=self.request.user,
                status=ProductAlert.ACTIVE)
            has_alert = alerts.exists()
        return has_alert

    def get_alert_form(self):
        return ProductAlertForm(
            user=self.request.user, product=self.object)

    def get_reviews(self):
        return self.object.reviews.filter(status=ProductReview.APPROVED)

    def send_signal(self, request, response, product):
        self.view_signal.send(
            sender=self, product=product, user=request.user, request=request,
            response=response)

    def get_template_names(self):
        """
        Return a list of possible templates.

        We try 2 options before defaulting to catalogue/detail.html:
            1). detail-for-upc-<upc>.html
            2). detail-for-class-<classname>.html

        This allows alternative templates to be provided for a per-product
        and a per-item-class basis.
        """
        return [
            '%s/detail-for-upc-%s.html' % (
                self.template_folder, self.object.upc),
            '%s/detail-for-class-%s.html' % (
                self.template_folder, self.object.get_product_class().slug),
            '%s/detail.html' % (self.template_folder)]


def get_product_base_queryset():
    """
    Deprecated. Kept only for backwards compatibility.
    Product.browsable.base_queryset() should be used instead.
    """
    warnings.warn(("`get_product_base_queryset` is deprecated in favour of"
                   "`base_queryset` on Product's managers. It will be removed"
                   "in Oscar 0.7."), DeprecationWarning)
    return Product.browsable.base_queryset()


class ProductCategoryView(ListView):
    """
    Browse products in a given category

    Category URLs used to be based on solely the slug. Renaming the category
    or any of the parent categories would break the URL. Hence, the new URLs
    consist of both the slug and category PK (compare product URLs).
    The legacy way still works to not break existing systems.
    """
    context_object_name = "products"
    template_name = 'catalogue/browse.html'
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE
    enforce_paths = True

    def get_object(self):
        if 'pk' in self.kwargs:
            self.category = get_object_or_404(Category, pk=self.kwargs['pk'])
        else:
            self.category = get_object_or_404(
                Category, slug=self.kwargs['category_slug'])

    def get(self, request, *args, **kwargs):
        self.get_object()
        self.categories = self.get_categories()

        if self.enforce_paths:
            # Categories are fetched by primary key to allow slug changes
            # If the slug has indeed changed, issue a redirect
            correct_path = self.category.get_absolute_url()
            if correct_path != request.path:
                return HttpResponsePermanentRedirect(correct_path)

        return super(ProductCategoryView, self).get(request, *args, **kwargs)

    def get_categories(self):
        """
        Return a list of the current category and it's ancestors
        """
        categories = list(self.category.get_descendants())
        categories.append(self.category)
        return categories

    def get_context_data(self, **kwargs):
        context = super(ProductCategoryView, self).get_context_data(**kwargs)

        context['categories'] = self.categories
        context['category'] = self.category
        context['summary'] = self.category.name
        return context

    def get_queryset(self):
        return Product.browsable.base_queryset().filter(
            categories__in=self.categories
        ).distinct()


class ProductListView(ListView):
    """
    A list of products
    """
    context_object_name = "products"
    template_name = 'catalogue/browse.html'
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE
    search_signal = product_search
    model = Product

    def get_search_query(self):
        q = self.request.GET.get('q', None)
        return q.strip() if q else q

    def get_queryset(self):
        q = self.get_search_query()
        qs = Product.browsable.base_queryset()
        if q:
            # Send signal to record this search
            self.search_signal.send(sender=self, query=q,
                                    user=self.request.user)
            return qs.filter(title__icontains=q)
        else:
            return qs

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        q = self.get_search_query()
        if not q:
            context['summary'] = _('All products')
        else:
            context['summary'] = _("Products matching '%(query)s'") \
                % {'query': q}
            context['search_term'] = q
        return context
