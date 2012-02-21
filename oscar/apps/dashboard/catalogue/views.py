from django.views import generic
from django.db.models import get_model
from django.contrib import messages
from django.core.urlresolvers import reverse

from oscar.core.loading import get_class
ProductForm = get_class('dashboard.catalogue.forms', 'ProductForm')
Product = get_model('catalogue', 'Product')


class ProductListView(generic.ListView):
    template_name = 'dashboard/catalogue/product_list.html'
    model = Product
    context_object_name = 'products'
    paginate_by = 20


class ProductUpdateView(generic.UpdateView):
    template_name = 'dashboard/catalogue/product_update.html'
    model = Product
    context_object_name = 'product'
    form_class = ProductForm

    def get_form_kwargs(self):
        kwargs = super(ProductUpdateView, self).get_form_kwargs()
        kwargs['product_class'] = self.object.product_class
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Updated product '%s'" %
                         self.object.title)
        return reverse('dashboard:catalogue-product-list')
