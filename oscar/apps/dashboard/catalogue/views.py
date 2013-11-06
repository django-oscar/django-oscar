from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views import generic
from django.db.models import get_model
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_classes
from oscar.views import sort_queryset

(ProductForm,
 ProductSearchForm,
 CategoryForm,
 StockRecordFormSet,
 StockAlertSearchForm,
 ProductCategoryFormSet,
 ProductImageFormSet,
 ProductRecommendationFormSet) = get_classes(
     'dashboard.catalogue.forms',
     ('ProductForm',
      'ProductSearchForm',
      'CategoryForm',
      'StockRecordFormSet',
      'StockAlertSearchForm',
      'ProductCategoryFormSet',
      'ProductImageFormSet',
      'ProductRecommendationFormSet'))
Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')
ProductImage = get_model('catalogue', 'ProductImage')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductClass = get_model('catalogue', 'ProductClass')
StockRecord = get_model('partner', 'StockRecord')
StockAlert = get_model('partner', 'StockAlert')
Partner = get_model('partner', 'Partner')


def get_queryset_for_user(user):
    """
    Returns all products the given user has access to.
    A staff user is allowed to access all Products.
    A non-staff user is only allowed access to a product if she's in at least
    one stock record's partner user list.
    """
    queryset = Product.objects.base_queryset().order_by('-date_created')
    if user.is_staff:
        return queryset.all()
    else:
        return queryset.filter(
            stockrecords__partner__users__pk=user.pk).distinct()


class ProductListView(generic.ListView):
    """
    Dashboard view of the product list.
    Supports the permission-based dashboard.
    """

    template_name = 'dashboard/catalogue/product_list.html'
    model = Product
    context_object_name = 'products'
    form_class = ProductSearchForm
    description_template = _(u'Products %(upc_filter)s %(title_filter)s')
    paginate_by = 20
    recent_products = 5

    def get_context_data(self, **kwargs):
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        ctx['product_classes'] = ProductClass.objects.all()
        ctx['form'] = self.form
        if 'recently_edited' in self.request.GET:
            ctx['queryset_description'] = _("Last %(num_products)d edited products") \
                % {'num_products': self.recent_products}
        else:
            ctx['queryset_description'] = self.description

        return ctx

    def get_queryset(self):
        """
        Build the queryset for this list and also update the title that
        describes the queryset
        """
        description_ctx = {'upc_filter': '',
                           'title_filter': ''}
        queryset = get_queryset_for_user(self.request.user)
        if 'recently_edited' in self.request.GET:
            # Just show recently edited
            queryset = queryset.order_by('-date_updated')
            queryset = queryset[:self.recent_products]
        else:
            # Allow sorting when all
            queryset = sort_queryset(queryset, self.request,
                                     ['title'], '-date_created')
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            self.description = self.description_template % description_ctx
            return queryset

        data = self.form.cleaned_data

        if data['upc']:
            queryset = queryset.filter(upc=data['upc'])
            description_ctx['upc_filter'] = _(
                " including an item with UPC '%s'") % data['upc']

        if data['title']:
            queryset = queryset.filter(
                title__icontains=data['title']).distinct()
            description_ctx['title_filter'] = _(
                " including an item with title matching '%s'") % data['title']

        self.description = self.description_template % description_ctx
        return queryset


class ProductCreateRedirectView(generic.RedirectView):
    permanent = False

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


class ProductCreateUpdateView(generic.UpdateView):
    """
    Dashboard view that bundles both creating and updating single products.
    Supports the permission-based dashboard.
    """

    template_name = 'dashboard/catalogue/product_update.html'
    model = Product
    context_object_name = 'product'

    form_class = ProductForm
    category_formset = ProductCategoryFormSet
    image_formset = ProductImageFormSet
    recommendations_formset = ProductRecommendationFormSet
    stockrecord_formset = StockRecordFormSet

    def get_object(self, queryset=None):
        """
        This parts allows generic.UpdateView to handle creating products as
        well. The only distinction between an UpdateView and a CreateView
        is that self.object is None. We emulate this behavior.
        Additionally, self.product_class is set.
        """
        user = self.request.user
        self.require_user_stockrecord = not user.is_staff
        self.creating = not 'pk' in self.kwargs
        if self.creating:
            try:
                product_class_id = self.kwargs.get('product_class_id', None)
                self.product_class = ProductClass.objects.get(
                    id=product_class_id)
            except ObjectDoesNotExist:
                raise Http404
            else:
                return None  # success
        else:
            product = super(ProductCreateUpdateView, self).get_object(queryset)
            user = self.request.user
            self.product_class = product.product_class
            # check user has permission to update Product
            if user.is_staff or product.is_user_a_partner_user(user):
                return product
            else:
                raise PermissionDenied

    def get_context_data(self, **kwargs):
        ctx = super(ProductCreateUpdateView, self).get_context_data(**kwargs)
        if 'stockrecord_formset' not in ctx:
            ctx['stockrecord_formset'] = self.stockrecord_formset(
                self.product_class, instance=self.object)
        if 'category_formset' not in ctx:
            ctx['category_formset'] = self.category_formset(instance=self.object)
        if 'image_formset' not in ctx:
            ctx['image_formset'] = self.image_formset(instance=self.object)
        if 'recommended_formset' not in ctx:
            ctx['recommended_formset'] = self.recommendations_formset(instance=self.object)
        if self.object is None:
            ctx['title'] = _('Create new %s product') % self.product_class.name
        else:
            ctx['title'] = ctx['product'].get_title()
        return ctx

    def get_form_kwargs(self):
        kwargs = super(ProductCreateUpdateView, self).get_form_kwargs()
        kwargs['product_class'] = self.product_class
        return kwargs

    def form_valid(self, form):
        return self.process_all_forms(form)

    def form_invalid(self, form):
        return self.process_all_forms(form)

    def process_all_forms(self, form):
        """
        Short-circuits the regular logic to have one place to have our
        logic to check all forms
        """
        # Need to create the product here because the inline forms need it
        # can't use commit=False because ProductForm does not support it
        if self.creating and form.is_valid():
            self.object = form.save()

        stockrecord_formset = self.stockrecord_formset(
            self.product_class,
            self.request.POST, instance=self.object)
        category_formset = self.category_formset(
            self.request.POST, instance=self.object)
        image_formset = self.image_formset(
            self.request.POST, self.request.FILES, instance=self.object)
        recommended_formset = self.recommendations_formset(
            self.request.POST, self.request.FILES, instance=self.object)

        is_valid = all([
            form.is_valid(),
            category_formset.is_valid(),
            image_formset.is_valid(),
            recommended_formset.is_valid(),
            stockrecord_formset.is_valid(),
        ])

        if is_valid:
            return self.forms_valid(
                form, stockrecord_formset, category_formset,
                image_formset, recommended_formset)
        else:
            # delete the temporary product again
            if self.creating and form.is_valid():
                self.object.delete()
                self.object = None
            return self.forms_invalid(
                form, stockrecord_formset, category_formset,
                image_formset, recommended_formset)

    def forms_valid(self, form, stockrecord_formset, category_formset,
                    image_formset, recommended_formset):
        """
        Save all changes and display a success url.
        """
        if not self.creating:
            # a just created product was already saved in process_all_forms()
            self.object = form.save()

        # Save formsets
        category_formset.save()
        image_formset.save()
        recommended_formset.save()
        stockrecord_formset.save()

        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, stockrecord_formset, category_formset,
                      image_formset, recommended_formset):
        messages.error(self.request,
                       _("Your submitted data was not valid - please "
                         "correct the below errors"))
        ctx = self.get_context_data(form=form,
                                    stockrecord_formset=stockrecord_formset,
                                    category_formset=category_formset,
                                    image_formset=image_formset,
                                    recommended_formset=recommended_formset)
        return self.render_to_response(ctx)

    def get_url_with_querystring(self, url):
        url_parts = [url]
        if self.request.GET.urlencode():
            url_parts += [self.request.GET.urlencode()]
        return "?".join(url_parts)

    def get_success_url(self):
        if self.creating:
            msg = _("Created product '%s'") % self.object.title
        else:
            msg = _("Updated product '%s'") % self.object.title
        messages.success(self.request, msg)
        url = reverse('dashboard:catalogue-product-list')
        if self.request.POST.get('action') == 'continue':
            url = reverse('dashboard:catalogue-product',
                          kwargs={"pk": self.object.id})
        return self.get_url_with_querystring(url)


class ProductDeleteView(generic.DeleteView):
    """
    Dashboard view to delete a product.
    Supports the permission-based dashboard.
    """
    template_name = 'dashboard/catalogue/product_delete.html'
    model = Product
    context_object_name = 'product'

    def get_object(self, queryset=None):
        product = super(ProductDeleteView, self).get_object(queryset)
        user = self.request.user
        if user.is_staff or product.is_user_a_partner_user(user):
            return product
        else:
            raise PermissionDenied

    def get_success_url(self):
        msg =_("Deleted product '%s'") % self.object.title
        messages.success(self.request, msg)
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
    context_object_name = 'category'

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
        ctx['title'] = _("Add a new category")
        return ctx

    def get_success_url(self):
        messages.info(self.request, _("Category created successfully"))
        return super(CategoryCreateView, self).get_success_url()


class CategoryUpdateView(CategoryListMixin, generic.UpdateView):
    template_name = 'dashboard/catalogue/category_form.html'
    model = Category
    form_class = CategoryForm

    def get_context_data(self, **kwargs):
        ctx = super(CategoryUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = _("Update category '%s'") % self.object.name
        return ctx

    def get_success_url(self):
        messages.info(self.request, _("Category updated successfully"))
        return super(CategoryUpdateView, self).get_success_url()


class CategoryDeleteView(CategoryListMixin, generic.DeleteView):
    template_name = 'dashboard/catalogue/category_delete.html'
    model = Category

    def get_context_data(self, *args, **kwargs):
        ctx = super(CategoryDeleteView, self).get_context_data(*args, **kwargs)
        ctx['parent'] = self.object.get_parent()
        return ctx

    def get_success_url(self):
        messages.info(self.request, _("Category deleted successfully"))
        return super(CategoryDeleteView, self).get_success_url()
