import os

from django.conf import settings
from django.contrib import messages
from django.core import exceptions
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import HttpResponse, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, View)

from oscar.core.loading import get_classes, get_model
from oscar.views.generic import BulkEditMixin

Range = get_model('offer', 'Range')
RangeProduct = get_model('offer', 'RangeProduct')
RangeProductFileUpload = get_model('offer', 'RangeProductFileUpload')
Product = get_model('catalogue', 'Product')
RangeForm, RangeProductForm = get_classes('dashboard.ranges.forms',
                                          ['RangeForm', 'RangeProductForm'])


class RangeListView(ListView):
    model = Range
    context_object_name = 'ranges'
    template_name = 'dashboard/ranges/range_list.html'


class RangeCreateView(CreateView):
    model = Range
    template_name = 'dashboard/ranges/range_form.html'
    form_class = RangeForm

    def get_success_url(self):
        if 'action' in self.request.POST:
            return reverse('dashboard:range-products',
                           kwargs={'pk': self.object.id})
        else:
            msg = render_to_string(
                'dashboard/ranges/messages/range_saved.html',
                {'range': self.object})
            messages.success(self.request, msg, extra_tags='safe noicon')
            return reverse('dashboard:range-list')

    def get_context_data(self, **kwargs):
        ctx = super(RangeCreateView, self).get_context_data(**kwargs)
        ctx['title'] = _("Create range")
        return ctx


class RangeUpdateView(UpdateView):
    model = Range
    template_name = 'dashboard/ranges/range_form.html'
    form_class = RangeForm

    def get_object(self):
        obj = super(RangeUpdateView, self).get_object()
        if not obj.is_editable:
            raise exceptions.PermissionDenied("Not allowed")
        return obj

    def get_success_url(self):
        if 'action' in self.request.POST:
            return reverse('dashboard:range-products',
                           kwargs={'pk': self.object.id})
        else:
            msg = render_to_string(
                'dashboard/ranges/messages/range_saved.html',
                {'range': self.object})
            messages.success(self.request, msg, extra_tags='safe noicon')
            return reverse('dashboard:range-list')

    def get_context_data(self, **kwargs):
        ctx = super(RangeUpdateView, self).get_context_data(**kwargs)
        ctx['range'] = self.object
        ctx['title'] = self.object.name
        return ctx


class RangeDeleteView(DeleteView):
    model = Range
    template_name = 'dashboard/ranges/range_delete.html'
    context_object_name = 'range'

    def get_success_url(self):
        messages.warning(self.request, _("Range deleted"))
        return reverse('dashboard:range-list')


class RangeProductListView(BulkEditMixin, ListView):
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
        products = self.get_range().all_products()
        return products.order_by('rangeproduct__display_order')

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
            range.remove_product(product)
        num_products = len(products)
        messages.success(request, ungettext("Removed %d product from range",
                                            "Removed %d products from range",
                                            num_products) % num_products)
        return HttpResponseRedirect(self.get_success_url(request))

    def add_products(self, request):
        range = self.get_range()
        form = self.form_class(range, request.POST, request.FILES)
        if not form.is_valid():
            ctx = self.get_context_data(form=form,
                                        object_list=self.object_list)
            return self.render_to_response(ctx)

        self.handle_query_products(request, range, form)
        self.handle_file_products(request, range, form)
        return HttpResponseRedirect(self.get_success_url(request))

    def handle_query_products(self, request, range, form):
        products = form.get_products()
        if not products:
            return

        for product in products:
            range.add_product(product)

        num_products = len(products)
        messages.success(request, ungettext("%d product added to range",
                                            "%d products added to range",
                                            num_products) % num_products)
        dupe_skus = form.get_duplicate_skus()
        if dupe_skus:
            messages.warning(
                request,
                _("The products with SKUs or UPCs matching %s are already "
                  "in this range") % ", ".join(dupe_skus))

        missing_skus = form.get_missing_skus()
        if missing_skus:
            messages.warning(
                request,
                _("No product(s) were found with SKU or UPC matching %s") %
                ", ".join(missing_skus))
        self.check_imported_products_sku_duplicates(request, products)

    def handle_file_products(self, request, range, form):
        if 'file_upload' not in request.FILES:
            return
        upload = self.create_upload_object(request, range)
        products = upload.process()
        if not upload.was_processing_successful():
            messages.error(request, upload.error_message)
        else:
            msg = render_to_string(
                'dashboard/ranges/messages/range_products_saved.html',
                {'range': range,
                 'upload': upload})
            messages.success(request, msg, extra_tags='safe noicon block')
        upload.delete_file()
        self.check_imported_products_sku_duplicates(request, products)

    def create_upload_object(self, request, range):
        f = request.FILES['file_upload']
        destination_path = os.path.join(settings.OSCAR_UPLOAD_ROOT, f.name)
        with open(destination_path, 'wb+') as dest:
            for chunk in f.chunks():
                dest.write(chunk)
        upload = RangeProductFileUpload.objects.create(
            range=range,
            uploaded_by=request.user,
            filepath=destination_path,
            size=f.size
        )
        return upload

    def check_imported_products_sku_duplicates(self, request, queryset):
        dupe_sku_products = queryset.values('stockrecords__partner_sku')\
                                    .annotate(total=Count('stockrecords__partner_sku'))\
                                    .filter(total__gt=1).order_by('stockrecords__partner_sku')
        if dupe_sku_products:
            dupe_skus = [p['stockrecords__partner_sku'] for p in dupe_sku_products]
            messages.warning(
                request,
                _("There are more than one product with SKU %s") %
                ", ".join(dupe_skus)
            )


class RangeReorderView(View):
    def post(self, request, pk):
        order = dict(request.POST).get('product')
        self._save_page_order(order)
        return HttpResponse(status=200)

    def _save_page_order(self, order):
        """
        Save the order of the products within range.
        """
        range = get_object_or_404(Range, pk=self.kwargs['pk'])
        for index, item in enumerate(order):
            entry = RangeProduct.objects.get(range=range, product__pk=item)
            if entry.display_order != index:
                entry.display_order = index
                entry.save()
