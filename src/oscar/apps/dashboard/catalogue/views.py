from django.views import generic
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_classes, get_model

from django_tables2 import SingleTableMixin

from oscar.views.generic import ObjectLookupView

(ProductSearchForm,
 CategoryForm,
 StockAlertSearchForm) \
    = get_classes('dashboard.catalogue.forms',
                  ('ProductSearchForm',
                   'CategoryForm',
                   'StockAlertSearchForm'))
ProductTable, CategoryTable \
    = get_classes('dashboard.catalogue.tables',
                  ('ProductTable', 'CategoryTable'))
Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')
ProductImage = get_model('catalogue', 'ProductImage')
ProductCategory = get_model('catalogue', 'ProductCategory')
StockRecord = get_model('partner', 'StockRecord')
StockAlert = get_model('partner', 'StockAlert')
Partner = get_model('partner', 'Partner')


def filter_products(queryset, user):
    """
    Restrict the queryset to products the given user has access to.
    A staff user is allowed to access all Products.
    A non-staff user is only allowed access to a product if they are in at
    least one stock record's partner user list.
    """
    if user.is_staff:
        return queryset

    return queryset.filter(stockrecords__partner__users__pk=user.pk).distinct()


class ProductListView(SingleTableMixin, generic.TemplateView):
    """
    Dashboard view of the product list.
    Supports the permission-based dashboard.
    """

    template_name = 'dashboard/catalogue/product_list.html'
    form_class = ProductSearchForm
    table_class = ProductTable
    context_table_name = 'products'

    def get_context_data(self, **kwargs):
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        ctx['form'] = self.form
        return ctx

    def get_description(self, form):
        if form.is_valid() and any(form.cleaned_data.values()):
            return _('Product search results')
        return _('Products')

    def get_table(self, **kwargs):
        if 'recently_edited' in self.request.GET:
            kwargs.update(dict(orderable=False))

        table = super(ProductListView, self).get_table(**kwargs)
        table.caption = self.get_description(self.form)
        return table

    def get_table_pagination(self):
        return dict(per_page=20)

    def filter_queryset(self, queryset):
        """
        Apply any filters to restrict the products that appear on the list
        """
        return filter_products(queryset, self.request.user)

    def get_queryset(self):
        """
        Build the queryset for this list
        """
        queryset = Product.browsable.base_queryset()
        queryset = self.filter_queryset(queryset)
        queryset = self.apply_search(queryset)
        return queryset

    def apply_search(self, queryset):
        """
        Filter the queryset and set the description according to the search
        parameters given
        """
        self.form = self.form_class(self.request.GET)

        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data.get('upc'):
            # If there's an exact UPC match, it returns just the matched
            # product. Otherwise does a broader icontains search.
            qs_match = queryset.filter(upc=data['upc'])
            if qs_match.exists():
                queryset = qs_match
            else:
                queryset = queryset.filter(upc__icontains=data['upc'])

        if data.get('title'):
            queryset = queryset.filter(title__icontains=data['title'])

        return queryset


class ProductDeleteView(generic.DeleteView):
    """
    Dashboard view to delete a product. Has special logic for deleting the
    last child product.
    Supports the permission-based dashboard.
    """
    template_name = 'dashboard/catalogue/product_delete.html'
    model = Product
    context_object_name = 'product'

    def get_queryset(self):
        """
        Filter products that the user doesn't have permission to update
        """
        return filter_products(Product.objects.all(), self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super(ProductDeleteView, self).get_context_data(**kwargs)
        if self.object.is_child:
            ctx['title'] = _("Delete product variant?")
        else:
            ctx['title'] = _("Delete product?")
        return ctx

    def delete(self, request, *args, **kwargs):
        # We override the core delete method and don't call super in order to
        # apply more sophisticated logic around handling child products.
        # Calling super makes it difficult to test if the product being deleted
        # is the last child.

        self.object = self.get_object()

        # Before performing the delete, record whether this product is the last
        # child.
        is_last_child = False
        if self.object.is_child:
            parent = self.object.parent
            is_last_child = parent.children.count() == 1

        # This also deletes any child products.
        self.object.delete()

        # If the product being deleted is the last child, then pass control
        # to a method than can adjust the parent itself.
        if is_last_child:
            self.handle_deleting_last_child(parent)

        return HttpResponseRedirect(self.get_success_url())

    def handle_deleting_last_child(self, parent):
        # If the last child product is deleted, this view defaults to turning
        # the parent product into a standalone product. While this is
        # appropriate for many scenarios, it is intentionally easily
        # overridable and not automatically done in e.g. a Product's delete()
        # method as it is more a UX helper than hard business logic.
        parent.structure = parent.STANDALONE
        parent.save()

    def get_success_url(self):
        """
        When deleting child products, this view redirects to editing the
        parent product. When deleting any other product, it redirects to the
        product list view.
        """
        if self.object.is_child:
            msg = _("Deleted product variant '%s'") % self.object.get_title()
            messages.success(self.request, msg)
            return reverse(
                'dashboard:catalogue-product',
                kwargs={'pk': self.object.parent_id})
        else:
            msg = _("Deleted product '%s'") % self.object.title
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


class CategoryListView(SingleTableMixin, generic.TemplateView):
    template_name = 'dashboard/catalogue/category_list.html'
    table_class = CategoryTable
    context_table_name = 'categories'

    def get_queryset(self):
        return Category.get_root_nodes()

    def get_context_data(self, *args, **kwargs):
        ctx = super(CategoryListView, self).get_context_data(*args, **kwargs)
        ctx['child_categories'] = Category.get_root_nodes()
        return ctx


class CategoryDetailListView(SingleTableMixin, generic.DetailView):
    template_name = 'dashboard/catalogue/category_list.html'
    model = Category
    context_object_name = 'category'
    table_class = CategoryTable
    context_table_name = 'categories'

    def get_table_data(self):
        return self.object.get_children()

    def get_context_data(self, *args, **kwargs):
        ctx = super(CategoryDetailListView, self).get_context_data(*args,
                                                                   **kwargs)
        ctx['child_categories'] = self.object.get_children()
        ctx['ancestors'] = self.object.get_ancestors_and_self()
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

    def get_initial(self):
        # set child category if set in the URL kwargs
        initial = super(CategoryCreateView, self).get_initial()
        if 'parent' in self.kwargs:
            initial['_ref_node_id'] = self.kwargs['parent']
        return initial


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


class ProductLookupView(ObjectLookupView):
    model = Product

    def get_lookup_queryset(self):
        return self.model.browsable.all()

    def lookup_filter(self, qs, term):
        return qs.filter(Q(title__icontains=term)
                         | Q(parent__title__icontains=term))
