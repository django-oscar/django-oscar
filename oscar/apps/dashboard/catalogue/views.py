from django.views import generic
from django.db.models import get_model
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from oscar.apps.dashboard.catalogue import forms
from oscar.core.loading import get_classes
ProductForm, StockRecordForm, StockAlertSearchForm, ProductCategoryFormSet, ProductImageFormSet = get_classes(
    'dashboard.catalogue.forms', ('ProductForm', 'StockRecordForm',
                                  'StockAlertSearchForm',
                                  'ProductCategoryFormSet',
                                  'ProductImageFormSet'))
Product = get_model('catalogue', 'Product')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductClass = get_model('catalogue', 'ProductClass')
StockRecord = get_model('partner', 'StockRecord')
StockAlert = get_model('partner', 'StockAlert')


class ProductListView(generic.ListView):
    template_name = 'dashboard/catalogue/product_list.html'
    model = Product
    context_object_name = 'products'
    form_class = forms.ProductSearchForm
    base_description = 'Products'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        ctx['product_classes'] = ProductClass.objects.all()
        ctx['form'] = self.form
        ctx['queryset_description'] = self.description
        return ctx

    def get_queryset(self):
        """
        Build the queryset for this list and also update the title that
        describes the queryset
        """
        self.description = self.base_description
        queryset = self.model.objects.all().order_by('-date_created')
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['upc']:
            queryset = queryset.filter(upc=data['upc'])
            self.description += " including an item with UPC '%s'" % data['upc']

        if data['title']:
            queryset = queryset.filter(title__icontains=data['title']).distinct()
            self.description += " including an item with title matching '%s'" % data['title']

        return queryset


class ProductCreateRedirectView(generic.RedirectView):

    def get_redirect_url(self, **kwargs):
        product_class_id = self.request.GET.get('product_class', None)
        if not product_class_id.isdigit():
            messages.error(self.request, "Please choose a product class")
            return reverse('dashboard:catalogue-product-list')
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
        if 'stockrecord_form' not in ctx:
            ctx['stockrecord_form'] = StockRecordForm()
        if 'category_formset' not in ctx:
            ctx['category_formset'] = ProductCategoryFormSet()
        if 'image_formset' not in ctx:
            ctx['image_formset'] = ProductImageFormSet()
        ctx['title'] = 'Create new product'
        return ctx

    def get_product_class(self):
        return ProductClass.objects.get(id=self.kwargs['product_class_id'])

    def get_form_kwargs(self):
        kwargs = super(ProductCreateView, self).get_form_kwargs()
        kwargs['product_class'] = self.get_product_class()
        return kwargs

    def form_invalid(self, form):
        stockrecord_form = StockRecordForm(self.request.POST)
        category_formset = ProductCategoryFormSet(self.request.POST)
        image_formset = ProductImageFormSet(self.request.POST, self.request.FILES)
        ctx = self.get_context_data(form=form,
                                    stockrecord_form=stockrecord_form,
                                    category_formset=category_formset,
                                    image_formset=image_formset)
        return self.render_to_response(ctx)

    def form_valid(self, form):
        product = form.save()

        stockrecord_form = StockRecordForm(self.request.POST)
        category_formset = ProductCategoryFormSet(self.request.POST,
                                                  instance=product)
        image_formset = ProductImageFormSet(self.request.POST,
                                            self.request.FILES,
                                            instance=product)
        if all([stockrecord_form.is_valid(), category_formset.is_valid(), image_formset.is_valid()]):
            # Save product
            product.save()
            # Save stock record
            stockrecord = stockrecord_form.save(commit=False)
            stockrecord.product = product
            stockrecord.save()
            # Save formsets
            category_formset.save()
            image_formset.save()
            return HttpResponseRedirect(self.get_success_url(product))

        # Delete product as its relations were not valid
        product.delete()

        ctx = self.get_context_data(form=form,
                                    stockrecord_form=stockrecord_form,
                                    category_formset=category_formset,
                                    image_formset=image_formset)
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
        if 'stockrecord_form' not in ctx:
            instance = None
            if self.object.has_stockrecord:
                instance=self.object.stockrecord
            ctx['stockrecord_form'] = StockRecordForm(instance=instance)
        if 'category_formset' not in ctx:
            ctx['category_formset'] = ProductCategoryFormSet(instance=self.object)
        if 'image_formset' not in ctx:
            ctx['image_formset'] = ProductImageFormSet(instance=self.object)
        ctx['title'] = 'Update product'
        return ctx

    def get_form_kwargs(self):
        kwargs = super(ProductUpdateView, self).get_form_kwargs()
        kwargs['product_class'] = self.object.product_class
        return kwargs

    def form_invalid(self, form):
        stockrecord_form = StockRecordForm(self.request.POST,
                                           instance=self.object.stockrecord)
        category_formset = ProductCategoryFormSet(self.request.POST,
                                                  instance=self.object)
        image_formset = ProductImageFormSet(self.request.POST,
                                            self.request.FILES,
                                            instance=self.object)
        ctx = self.get_context_data(form=form,
                                    stockrecord_form=stockrecord_form,
                                    category_formset=category_formset,
                                    image_formset=image_formset)
        return self.render_to_response(ctx)


    def form_valid(self, form):
        stockrecord_form = StockRecordForm(self.request.POST,
                                           instance=self.object.stockrecord)
        category_formset = ProductCategoryFormSet(self.request.POST,
                                                  instance=self.object)
        image_formset = ProductImageFormSet(self.request.POST,
                                            self.request.FILES,
                                            instance=self.object)
        if all([stockrecord_form.is_valid(), category_formset.is_valid(), image_formset.is_valid()]):
            form.save()
            stockrecord_form.save()
            category_formset.save()
            image_formset.save()
            return HttpResponseRedirect(self.get_success_url())

        ctx = self.get_context_data(form=form,
                                    stockrecord_form=stockrecord_form,
                                    category_formset=category_formset,
                                    image_formset=image_formset)
        return self.render_to_response(ctx)

    def get_success_url(self):
        messages.success(self.request, "Updated product '%s'" %
                         self.object.title)
        return reverse('dashboard:catalogue-product-list')


class StockAlertListView(generic.ListView):
    template_name = 'dashboard/catalogue/stockalert_list.html'
    model = StockAlert
    context_object_name = 'alerts'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super(StockAlertListView, self).get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['description'] = self.description
        return ctx

    def get_queryset(self):
        if 'status' in self.request.GET:
            self.form = StockAlertSearchForm(self.request.GET)
            if self.form.is_valid():
                status = self.form.cleaned_data['status']
                self.description = 'Alerts with status "%s"' % status
                return self.model.objects.filter(status=status)
        else:
            self.description = 'All alerts'
            self.form = StockAlertSearchForm()
        return self.model.objects.all()
