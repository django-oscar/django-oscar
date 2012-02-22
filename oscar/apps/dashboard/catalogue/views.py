from django.views import generic
from django.db.models import get_model
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from oscar.core.loading import get_classes
ProductForm, StockRecordForm = get_classes('dashboard.catalogue.forms', ('ProductForm', 'StockRecordForm'))
Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
StockRecord = get_model('partner', 'StockRecord')


class ProductListView(generic.ListView):
    template_name = 'dashboard/catalogue/product_list.html'
    model = Product
    context_object_name = 'products'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        ctx['product_classes'] = ProductClass.objects.all()
        return ctx


class ProductCreateRedirectView(generic.RedirectView):

    def get_redirect_url(self, **kwargs):
        product_class_id = self.request.GET.get('product_class', None)
        try:
            product_class = ProductClass.objects.get(id=product_class_id)
        except ProductClass.DoesNotExist:
            messages.error(self.request, "Please choose a product class")
            return reverse('dashboard:catalogue-product-list')
        else:
            return reverse('dashboard:catalogue-product-create',
                           kwargs={'product_class_id': product_class.id})


class ProductCreateView(generic.CreateView):
    template_name = 'dashboard/catalogue/product_update.html'
    model = Product
    context_object_name = 'product'
    form_class = ProductForm

    def get_context_data(self, **kwargs):
        ctx = super(ProductCreateView, self).get_context_data(**kwargs)
        ctx['stockrecord_form'] = StockRecordForm()
        ctx['title'] = 'Create new product'
        return ctx

    def get_product_class(self):
        return ProductClass.objects.get(id=self.kwargs['product_class_id'])

    def get_form_kwargs(self):
        kwargs = super(ProductCreateView, self).get_form_kwargs()
        kwargs['product_class'] = self.get_product_class()
        return kwargs

    def form_valid(self, form):
        stockrecord_form = StockRecordForm(self.request.POST)
        if stockrecord_form.is_valid():
            # Save product
            product = form.save()
            product.product_class = self.get_product_class()
            product.save()
            # Save stock record
            stockrecord = stockrecord_form.save(commit=False)
            stockrecord.product = product
            stockrecord.save()
            return HttpResponseRedirect(self.get_success_url(product))

        ctx = self.get_context_data()
        ctx['form'] = form
        ctx['stockrecord_form'] = stockrecord_form
        return self.render_to_response(ctx)

    def get_success_url(self, product):
        messages.success(self.request, "Created product '%s'" % product.title)
        return reverse('dashboard:catalogue-product-list')


class ProductUpdateView(generic.UpdateView):
    template_name = 'dashboard/catalogue/product_update.html'
    model = Product
    context_object_name = 'product'
    form_class = ProductForm

    def get_context_data(self, **kwargs):
        ctx = super(ProductUpdateView, self).get_context_data(**kwargs)
        ctx['stockrecord_form'] = StockRecordForm(instance=self.object.stockrecord)
        ctx['title'] = 'Update product'
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
