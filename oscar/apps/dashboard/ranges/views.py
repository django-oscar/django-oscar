from django.views.generic import (ListView, DeleteView, CreateView, UpdateView)
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.template.defaultfilters import pluralize

from oscar.views.generic import BulkEditMixin
from oscar.core.loading import get_class

Range = get_model('offer', 'Range')
Product = get_model('catalogue', 'Product')
RangeProductForm = get_class('dashboard.ranges.forms', 'RangeProductForm')


class RangeListView(ListView):
    model = Range
    context_object_name = 'ranges'
    template_name = 'dashboard/ranges/range_list.html'


class RangeCreateView(CreateView):
    model = Range
    template_name = 'dashboard/ranges/range_form.html'

    def get_success_url(self):
        messages.success(self.request, "Range created")
        return reverse('dashboard:range-list')


class RangeUpdateView(UpdateView):
    model = Range
    template_name = 'dashboard/ranges/range_form.html'

    def get_success_url(self):
        messages.success(self.request, "Range updated")
        return reverse('dashboard:range-list')


class RangeDeleteView(DeleteView):
    model = Range
    template_name = 'dashboard/ranges/range_delete.html'
    context_object_name = 'range'

    def get_success_url(self):
        messages.warning(self.request, "Range deleted")
        return reverse('dashboard:range-list')


class RangeProductListView(ListView, BulkEditMixin):
    model = Product
    template_name = 'dashboard/ranges/range_product_list.html'
    context_object_name = 'products'
    actions = ('remove_selected_products', 'add_products')
    form_class = RangeProductForm

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if request.POST.get('action', None) == 'add_products':
            return self.add_products(request)
        return super(RangeProductListView, self).post(request, *args, **kwargs)

    def get_range(self):
        if not hasattr(self, '_range'):
            self._range = get_object_or_404(Range, id=self.kwargs['pk'])
        return self._range

    def get_queryset(self):
        return self.get_range().included_products.all()

    def get_context_data(self, **kwargs):
        ctx = super(RangeProductListView, self).get_context_data(**kwargs)
        range = self.get_range()
        ctx['range'] = range
        if 'form' not in ctx:
            ctx['form'] = self.form_class(range)
        return ctx

    def remove_selected_products(self, request, products):
        range = self.get_range()
        for product in products:
            range.included_products.remove(product)
        messages.success(request, 'Removed %d products from range' %
                         len(products))
        return HttpResponseRedirect(self.get_success_url(request))

    def add_products(self, request):
        range = self.get_range()
        form = self.form_class(range, request.POST)
        if not form.is_valid():
            ctx = self.get_context_data(form=form, object_list=self.object_list)
            return self.render_to_response(ctx)

        products = form.get_products()
        for product in products:
            range.included_products.add(product)

        num_products = len(products)
        messages.success(request, "%d product%s added to range" % (
            num_products, pluralize(num_products)))

        dupe_skus = form.get_duplicate_skus()
        if dupe_skus:
            messages.warning(
                request,
                "The products with SKUs matching %s are already in this range" % (", ".join(dupe_skus)))

        missing_skus = form.get_missing_skus()
        if missing_skus:
            messages.warning(request,
                             "No product was found with SKU matching %s" % ', '.join(missing_skus))

        return HttpResponseRedirect(self.get_success_url(request))
