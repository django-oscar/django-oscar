from django.views import generic
from django.db.models import get_model
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from oscar.apps.dashboard.catalogue import forms
from oscar.core.loading import get_classes

ProductForm, CategoryForm, StockRecordForm, StockAlertSearchForm, ProductCategoryFormSet, ProductImageFormSet = get_classes(
    'dashboard.catalogue.forms', ('ProductForm', 'CategoryForm', 'StockRecordForm',
                                  'StockAlertSearchForm',
                                  'ProductCategoryFormSet',
                                  'ProductImageFormSet'))
Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductClass = get_model('catalogue', 'ProductClass')
StockRecord = get_model('partner', 'StockRecord')
StockAlert = get_model('partner', 'StockAlert')


class ProductListView(generic.ListView):
    template_name = 'dashboard/catalogue/product_list.html'
    model = Product
    context_object_name = 'products'
    form_class = forms.ProductSearchForm
    description_template = _(u'Products %(upc_filter)s %(title_filter)s')
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
        description_ctx = {'upc_filter': '',
                           'title_filter': ''}
        queryset = self.model.objects.all().order_by('-date_created').prefetch_related(
            'product_class', 'stockrecord__partner')
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            self.description = self.description_template % description_ctx
            return queryset

        data = self.form.cleaned_data

        if data['upc']:
            queryset = queryset.filter(upc=data['upc'])
            description_ctx['upc_filter'] = _(" including an item with UPC '%s'") % data['upc']

        if data['title']:
            queryset = queryset.filter(title__icontains=data['title']).distinct()
            description_ctx['title_filter'] = _(" including an item with title matching '%s'") % data['title']

        self.description = self.description_template % description_ctx
        return queryset


class ProductCreateRedirectView(generic.RedirectView):

    def get_redirect_url(self, **kwargs):
        product_class_id = self.request.GET.get('product_class', None)
        if not product_class_id or not product_class_id.isdigit():
            messages.error(self.request, _("Please choose a product class"))
            return reverse('dashboard:catalogue-product-list')
        try:
            product_class = ProductClass.objects.get(id=product_class_id)
        except ProductClass.DoesNotExist:
            messages.error(self.request, _("Please choose a product class"))
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
        ctx['title'] = _('Create new product')
        ctx['product_class'] = self.get_product_class()
        return ctx

    def get_product_class(self):
        return ProductClass.objects.get(id=self.kwargs['product_class_id'])

    def get_form_kwargs(self):
        kwargs = super(ProductCreateView, self).get_form_kwargs()
        kwargs['product_class'] = self.get_product_class()
        return kwargs

    def is_stockrecord_submitted(self):
        return len(self.request.POST.get('partner', '')) > 0

    def form_invalid(self, form):
        if self.is_stockrecord_submitted():
            stockrecord_form = StockRecordForm(self.request.POST)
        else:
            stockrecord_form = StockRecordForm()
        category_formset = ProductCategoryFormSet(self.request.POST)
        image_formset = ProductImageFormSet(self.request.POST, self.request.FILES)

        messages.error(self.request,
                       _("Your submitted data was not valid - please "
                         "correct the below errors"))
        ctx = self.get_context_data(form=form,
                                    stockrecord_form=stockrecord_form,
                                    category_formset=category_formset,
                                    image_formset=image_formset)
        return self.render_to_response(ctx)

    def form_valid(self, form):
        product = form.save()
        category_formset = ProductCategoryFormSet(self.request.POST,
                                                  instance=product)
        image_formset = ProductImageFormSet(self.request.POST,
                                            self.request.FILES,
                                            instance=product)
        if self.is_stockrecord_submitted():
            stockrecord_form = StockRecordForm(self.request.POST)
            is_valid = all([stockrecord_form.is_valid(),
                            category_formset.is_valid(),
                            image_formset.is_valid()])
        else:
            stockrecord_form = StockRecordForm()
            is_valid = all([category_formset.is_valid(),
                            image_formset.is_valid()])
        if is_valid:
            if self.is_stockrecord_submitted():
                # Save stock record
                stockrecord = stockrecord_form.save(commit=False)
                stockrecord.product = product
                stockrecord.save()
            # Save formsets
            category_formset.save()
            image_formset.save()
            return HttpResponseRedirect(self.get_success_url(product))

        messages.error(self.request,
                       _("Your submitted data was not valid - please "
                         "correct the below errors"))

        # Delete product as its relations were not valid
        product.delete()
        ctx = self.get_context_data(form=form,
                                    stockrecord_form=stockrecord_form,
                                    category_formset=category_formset,
                                    image_formset=image_formset)
        return self.render_to_response(ctx)

    def get_success_url(self, product):
        messages.success(self.request, _("Created product '%s'") % product.title)
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
        ctx['title'] = _('Update product')
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
        stockrecord = None
        if self.object.has_stockrecord:
            stockrecord = self.object.stockrecord
        stockrecord_form = StockRecordForm(self.request.POST,
                                           instance=stockrecord)
        category_formset = ProductCategoryFormSet(self.request.POST,
                                                  instance=self.object)
        image_formset = ProductImageFormSet(self.request.POST,
                                            self.request.FILES,
                                            instance=self.object)
        if all([stockrecord_form.is_valid(),
                category_formset.is_valid(),
                image_formset.is_valid()]):
            form.save()
            stockrecord = stockrecord_form.save()
            stockrecord.product = self.object
            stockrecord.save()
            category_formset.save()
            image_formset.save()
            return HttpResponseRedirect(self.get_success_url())

        ctx = self.get_context_data(form=form,
                                    stockrecord_form=stockrecord_form,
                                    category_formset=category_formset,
                                    image_formset=image_formset)
        return self.render_to_response(ctx)

    def get_success_url(self):
        messages.success(self.request, _("Updated product '%s'") %
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
                self.description = _('Alerts with status "%s"') % status
                return self.model.objects.filter(status=status)
        else:
            self.description = _('All alerts')
            self.form = StockAlertSearchForm()
        return self.model.objects.all()


class CategoryListView(generic.TemplateView):
    template_name = 'dashboard/catalogue/category_list.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(CategoryListView, self).get_context_data(*args, **kwargs)
        ctx['child_categories'] = Category.get_root_nodes()
        return ctx


class CategoryDetailListView(generic.DetailView):
    template_name = 'dashboard/catalogue/category_list.html'
    model = Category

    def get_context_data(self, *args, **kwargs):
        ctx = super(CategoryDetailListView, self).get_context_data(*args, **kwargs)
        ctx['child_categories'] = self.object.get_children()
        ctx['ancestors'] = self.object.get_ancestors()
        return ctx


class CategoryListMixin(object):

    def get_success_url(self):
        parent = self.object.get_parent()
        if parent is None:
            return reverse("dashboard:catalogue-category-list")
        else:
            return reverse("dashboard:catalogue-category-detail-list", 
                            args=(parent.pk,))


class CategoryCreateView(CategoryListMixin, generic.CreateView):
    template_name = 'dashboard/catalogue/category_form.html'
    model = Category
    form_class = CategoryForm

    def get_context_data(self, **kwargs):
        ctx = super(CategoryCreateView, self).get_context_data(**kwargs)
        ctx['title'] = "Add a new category"
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Category created successfully")
        return super(CategoryCreateView, self).get_success_url()


class CategoryUpdateView(CategoryListMixin, generic.UpdateView):
    template_name = 'dashboard/catalogue/category_form.html'
    model = Category
    form_class = CategoryForm

    def get_context_data(self, **kwargs):
        ctx = super(CategoryUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = "Update category '%s'" % self.object.name
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Category updated successfully")
        return super(CategoryUpdateView, self).get_success_url()


class CategoryDeleteView(CategoryListMixin, generic.DeleteView):
    template_name = 'dashboard/catalogue/category_delete.html'
    model = Category

    def get_context_data(self, *args, **kwargs):
        ctx = super(CategoryDeleteView, self).get_context_data(*args, **kwargs)
        ctx['parent'] = self.object.get_parent()
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Category deleted successfully")
        return super(CategoryDeleteView, self).get_success_url()
