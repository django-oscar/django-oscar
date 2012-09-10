import os
from django.views.generic import (ListView, DeleteView, CreateView, UpdateView)
from django.utils.translation import ungettext, ugettext_lazy as _
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings

from oscar.views.generic import BulkEditMixin
from oscar.core.loading import get_classes

Range = get_model('offer', 'Range')
Product = get_model('catalogue', 'Product')
RangeForm, RangeProductForm = get_classes('dashboard.ranges.forms',
                                          ['RangeForm', 'RangeProductForm'])

RangeProductFileUpload = get_model('ranges', 'RangeProductFileUpload')


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
            return reverse('dashboard:range-products', kwargs={'pk': self.object.id})
        else:
            messages.success(self.request, _("Range created"))
            return reverse('dashboard:range-list')

    def get_context_data(self, **kwargs):
        ctx = super(RangeCreateView, self).get_context_data(**kwargs)
        ctx['title'] = _("Create range")
        return ctx


class RangeUpdateView(UpdateView):
    model = Range
    template_name = 'dashboard/ranges/range_form.html'
    form_class = RangeForm

    def get_success_url(self):
        if 'action' in self.request.POST:
            return reverse('dashboard:range-products', kwargs={'pk': self.object.id})
        else:
            messages.success(self.request, _("Range updated"))
            return reverse('dashboard:range-list')

    def get_context_data(self, **kwargs):
        ctx = super(RangeUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = _("Update range")
        return ctx


class RangeDeleteView(DeleteView):
    model = Range
    template_name = 'dashboard/ranges/range_delete.html'
    context_object_name = 'range'

    def get_success_url(self):
        messages.warning(self.request, _("Range deleted"))
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
        num_products = len(products)
        messages.success(request, ungettext("Removed %d product from range",
                                            "Removed %d products from range",
                                            num_products) % num_products)
        return HttpResponseRedirect(self.get_success_url(request))

    def add_products(self, request):
        range = self.get_range()
        form = self.form_class(range, request.POST, request.FILES)
        if not form.is_valid():
            ctx = self.get_context_data(form=form, object_list=self.object_list)
            return self.render_to_response(ctx)

        self.handle_query_products(request, range, form)
        self.handle_file_products(request, range, form)
        return HttpResponseRedirect(self.get_success_url(request))

    def handle_query_products(self, request, range, form):
        products = form.get_products()
        if not products:
            return

        for product in products:
            range.included_products.add(product)

        num_products = len(products)
        messages.success(request, ungettext("%d product added to range",
                                            "%d products added to range",
                                            num_products) % num_products)
        dupe_skus = form.get_duplicate_skus()
        if dupe_skus:
            messages.warning(
                request,
                _("The products with SKUs or UPCs matching %s are already in this range") % ", ".join(dupe_skus))

        missing_skus = form.get_missing_skus()
        if missing_skus:
            messages.warning(request,
                             _("No product(s) were found with SKU or UPC matching %s") % ", ".join(missing_skus))

    def handle_file_products(self, request, range, form):
        if not 'file_upload' in request.FILES:
            return 
        upload = self.create_upload_object(request, range)
        upload.process()
        if not upload.was_processing_successful():
            messages.error(request, upload.error_message)
        else:
            msg = _("File processed: %(new_skus)d products added, "
                    "%(dupe_skus)d duplicate identifiers, "
                    "%(unknown_skus)d identifiers were not found") % {
                        'new_skus': upload.num_new_skus,
                        'dupe_skus': upload.num_duplicate_skus,
                        'unknown_skus': upload.num_unknown_skus
                    }
            if upload.num_new_skus:
                messages.success(request, msg)
            else:
                messages.warning(request, msg)
        upload.delete_file()

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
