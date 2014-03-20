from django.utils.http import urlquote
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class, get_model
from oscar.apps.catalogue.signals import product_viewed

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

            expected_path = product.get_absolute_url()
            if expected_path != urlquote(request.path):
                return HttpResponsePermanentRedirect(expected_path)

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
        reviews = self.get_reviews()
        ctx['reviews'] = reviews
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


class ProductCategoryView(ListView):
    """
    Browse products in a given category
    """
    context_object_name = "products"
    template_name = 'catalogue/browse.html'
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE
    enforce_paths = True

    def get_object(self):
        if 'pk' in self.kwargs:
            # Usual way to reach a category page. We just look at the primary
            # key in case the slug changed. If it did, get() will redirect
            # appropriately
            self.category = get_object_or_404(Category, pk=self.kwargs['pk'])
        elif 'category_slug' in self.kwargs:
            # For SEO reasons, we allow chopping off bits of the URL. If that
            # happened, no primary key will be available.
            self.category = get_object_or_404(
                Category, slug=self.kwargs['category_slug'])
        else:
            # If neither slug nor primary key are given, we show all products
            self.category = None

    def get(self, request, *args, **kwargs):
        self.get_object()
        if self.enforce_paths and self.category is not None:
            # Categories are fetched by primary key to allow slug changes.
            # If the slug has indeed changed, issue a redirect.
            expected_path = self.category.get_absolute_url()
            if expected_path != urlquote(request.path):
                return HttpResponsePermanentRedirect(expected_path)
        return super(ProductCategoryView, self).get(request, *args, **kwargs)

    def get_categories(self):
        """
        Return a list of the current category and it's ancestors
        """
        return list(self.category.get_descendants()) + [self.category]

    def get_summary(self):
        """
        Summary to be shown in template
        """
        return self.category.name if self.category else _('All products')

    def get_context_data(self, **kwargs):
        context = super(ProductCategoryView, self).get_context_data(**kwargs)
        context['category'] = self.category
        context['summary'] = self.get_summary()
        return context

    def get_queryset(self):
        qs = Product.browsable.base_queryset()
        if self.category is not None:
            categories = self.get_categories()
            qs = qs.filter(categories__in=categories).distinct()
        return qs
