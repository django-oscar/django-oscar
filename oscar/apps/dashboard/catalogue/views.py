from django.views import generic
from django.db.models import get_model
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from oscar.core.loading import get_classes
ProductForm, StockRecordForm = get_classes('dashboard.catalogue.forms', ('ProductForm', 'StockRecordForm'))
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')


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

    def get_context_data(self, **kwargs):
        ctx = super(ProductUpdateView, self).get_context_data(**kwargs)
        ctx['stockrecord_form'] = StockRecordForm(instance=self.object.stockrecord)
        return ctx

    def get_form_kwargs(self):
        kwargs = super(ProductUpdateView, self).get_form_kwargs()
        kwargs['product_class'] = self.object.product_class
        return kwargs

    def form_valid(self, form):
        stockrecord_form = StockRecordForm(self.request.POST,
                                           instance=self.object.stockrecord)
        if stockrecord_form.is_valid():
            form.save()
            stockrecord_form.save()
            return HttpResponseRedirect(self.get_success_url())

        ctx = self.get_context_data()
        ctx['form'] = form
        ctx['stockrecord_form'] = stockrecord_form
        return self.render_to_response(ctx)

    def get_success_url(self):
        messages.success(self.request, "Updated product '%s'" %
                         self.object.title)
        return reverse('dashboard:catalogue-product-list')
