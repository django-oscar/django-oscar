from django.views.generic import (ListView, DeleteView, CreateView, UpdateView)
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from oscar.views.generic import BulkEditMixin
from oscar.core.loading import get_classes

Range = get_model('offer', 'Range')
Product = get_model('catalogue', 'Product')
RangeProductForm = get_classes('dashboard.ranges.forms', ['RangeProductForm'])


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
    actions = ('remove_selected_products')

    def get_range(self):
        if not hasattr(self, '_range'):
            self._range = get_object_or_404(Range, id=self.kwargs['pk'])
        return self._range

    def get_queryset(self):
        return self.get_range().included_products.all()

    def get_context_data(self, **kwargs):
        ctx = super(RangeProductListView, self).get_context_data(**kwargs)
        ctx['range'] = self.get_range()
        return ctx

    def remove_selected_products(self, request, products):
        range = self.get_range()
        for product in products:
            range.included_products.remove(product)
        messages.success(request, 'Removed %d products from range' %
                         len(products))
        return HttpResponseRedirect(self.get_success_url(request))
