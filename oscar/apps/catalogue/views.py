from django.http import HttpResponsePermanentRedirect, Http404
from django.views.generic import ListView, DetailView
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class
from oscar.apps.catalogue.signals import product_viewed, product_search

Product = get_model('catalogue', 'product')
ProductReview = get_model('reviews', 'ProductReview')
Category = get_model('catalogue', 'category')
ProductAlert = get_model('customer', 'ProductAlert')
ProductAlertForm = get_class('customer.forms',
                             'ProductAlertForm')


class ProductDetailView(DetailView):
    context_object_name = 'product'
    model = Product
    view_signal = product_viewed
    template_folder = "catalogue"

    def get_object(self):
        # Use a cached version to prevent unnecessary DB calls
        if not hasattr(self, '_product'):
            setattr(self, '_product',
                    super(ProductDetailView, self).get_object())
        return self._product

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
            has_alert = alerts.count() > 0
        return has_alert

    def get_alert_form(self):
        return ProductAlertForm(user=self.request.user,
                                product=self.object)

    def get_reviews(self):
        return self.object.reviews.filter(status=ProductReview.APPROVED)

    def get(self, request, **kwargs):
        # Ensure that the correct URL is used
        product = self.get_object()
        correct_path = product.get_absolute_url()
        if correct_path != request.path:
            return HttpResponsePermanentRedirect(correct_path)

        response = super(ProductDetailView, self).get(request, **kwargs)
        self.send_signal(request, response, product)
        return response

    def send_signal(self, request, response, product):
        self.view_signal.send(sender=self, product=product, user=request.user,
                              request=request, response=response)

    def get_template_names(self):
        """
        Return a list of possible templates.

        We try 2 options before defaulting to catalogue/detail.html:
        1). detail-for-upc-<upc>.html
        2). detail-for-class-<classname>.html

        This allows alternative templates to be provided for a per-product
        and a per-item-class basis.
        """
        product = self.get_object()
        names = ['%s/detail-for-upc-%s.html' % (self.template_folder, product.upc),
                 '%s/detail-for-class-%s.html' % (self.template_folder, product.product_class.name.lower()),
                 '%s/detail.html' % (self.template_folder)]
        return names


def get_product_base_queryset():
    """
    Return ``QuerySet`` for product model with related
    content pre-loaded. The ``QuerySet`` returns unfiltered
    results for further filtering.
    """
    return Product.browsable.select_related(
        'product_class',
    ).prefetch_related(
        'reviews',
        'variants',
        'product_options',
        'product_class__options',
        'stockrecord',
        'stockrecord__partner',
        'images',
    ).all()


class ProductCategoryView(ListView):
    """
    Browse products in a given category
    """
    context_object_name = "products"
    template_name = 'catalogue/browse.html'
    paginate_by = 20

    def get_categories(self):
        """
        Return a list of the current category and it's ancestors
        """
        slug = self.kwargs['category_slug']
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            raise Http404()
        categories = list(category.get_descendants())
        categories.append(category)
        return categories

    def get_context_data(self, **kwargs):
        context = super(ProductCategoryView, self).get_context_data(**kwargs)

        categories = self.get_categories()
        context['categories'] = categories
        context['category'] = categories[-1]
        context['summary'] = categories[-1].name
        return context

    def get_queryset(self):
        return get_product_base_queryset().filter(
            categories__in=self.get_categories()
        ).distinct()


class ProductListView(ListView):
    """
    A list of products
    """
    context_object_name = "products"
    template_name = 'catalogue/browse.html'
    paginate_by = 20
    search_signal = product_search
    model = Product

    def get_search_query(self):
        q = self.request.GET.get('q', None)
        return q.strip() if q else q

    def get_queryset(self):
        q = self.get_search_query()
        if q:
            # Send signal to record the view of this product
            self.search_signal.send(sender=self, query=q, user=self.request.user)
            return get_product_base_queryset().filter(title__icontains=q)
        else:
            return get_product_base_queryset()

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        q = self.get_search_query()
        if not q:
            context['summary'] = _('All products')
        else:
            context['summary'] = _("Products matching '%(query)s'") % {'query': q}
            context['search_term'] = q
        return context
