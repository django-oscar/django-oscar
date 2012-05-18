from django.views.generic import (ListView, FormView, DetailView, DeleteView)
from django.db.models.loading import get_model
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from oscar.core.loading import get_class
VoucherForm = get_class('dashboard.vouchers.forms', 'VoucherForm')

Voucher = get_model('voucher', 'Voucher')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Benefit = get_model('offer', 'Benefit')
Condition = get_model('offer', 'Condition')
OrderDiscount = get_model('order', 'OrderDiscount')


class VoucherListView(ListView):
    model = Voucher
    context_object_name = 'vouchers'
    template_name = 'dashboard/vouchers/voucher_list.html'


class VoucherCreateView(FormView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_form.html'
    form_class = VoucherForm

    def get_context_data(self, **kwargs):
        ctx = super(VoucherCreateView, self).get_context_data(**kwargs)
        ctx['title'] = 'Create voucher'
        return ctx

    def form_valid(self, form):
        # Create offer and benefit
        condition = Condition.objects.create(
            range=form.cleaned_data['benefit_range'],
            type=Condition.COUNT,
            value=1
        )
        benefit = Benefit.objects.create(
            range=form.cleaned_data['benefit_range'],
            type=form.cleaned_data['benefit_type'],
            value=form.cleaned_data['benefit_value']
        )
        name = form.cleaned_data['name']
        offer = ConditionalOffer.objects.create(
            name="Offer for voucher '%s'" % name,
            offer_type="Voucher",
            benefit=benefit,
            condition=condition,
        )
        voucher = Voucher.objects.create(
            name=name,
            code=form.cleaned_data['code'],
            usage=form.cleaned_data['usage'],
            start_date=form.cleaned_data['start_date'],
            end_date=form.cleaned_data['end_date'],
        )
        voucher.offers.add(offer)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, "Voucher created")
        return reverse('dashboard:voucher-list')


class VoucherStatsView(DetailView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_detail.html'
    context_object_name = 'voucher'

    def get_context_data(self, **kwargs):
        ctx = super(VoucherStatsView, self).get_context_data(**kwargs)
        ctx['discounts'] = OrderDiscount.objects.filter(voucher_id=self.object.id).order_by('-order__date_placed')
        return ctx


class VoucherUpdateView(FormView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_form.html'
    form_class = VoucherForm

    def get_voucher(self):
        if not hasattr(self, 'voucher'):
            self.voucher = Voucher.objects.get(id=self.kwargs['pk'])
        return self.voucher

    def get_context_data(self, **kwargs):
        ctx = super(VoucherUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = 'Update voucher'
        return ctx

    def get_form_kwargs(self):
        kwargs = super(VoucherUpdateView, self).get_form_kwargs()
        kwargs['voucher'] = self.get_voucher()
        return kwargs

    def get_initial(self):
        voucher = self.get_voucher()
        offer = voucher.offers.all()[0]
        benefit = offer.benefit
        return {
            'name': voucher.name,
            'code': voucher.code,
            'start_date': voucher.start_date,
            'end_date': voucher.end_date,
            'usage': voucher.usage,
            'benefit_type': benefit.type,
            'benefit_range': benefit.range,
            'benefit_value': benefit.value,
        }

    def form_valid(self, form):
        voucher = self.get_voucher()
        voucher.name = form.cleaned_data['name']
        voucher.code = form.cleaned_data['code']
        voucher.usage = form.cleaned_data['usage']
        voucher.start_date = form.cleaned_data['start_date']
        voucher.end_date = form.cleaned_data['end_date']
        voucher.save()

        offer = voucher.offers.all()[0]
        offer.condition.range = form.cleaned_data['benefit_range']
        offer.condition.save()

        benefit = voucher.benefit
        benefit.range = form.cleaned_data['benefit_range']
        benefit.type = form.cleaned_data['benefit_type']
        benefit.value = form.cleaned_data['benefit_value']
        benefit.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, "Voucher updated")
        return reverse('dashboard:voucher-list')


class VoucherDeleteView(DeleteView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_delete.html'
    context_object_name = 'voucher'

    def get_success_url(self):
        messages.warning(self.request, "Voucher deleted")
        return reverse('dashboard:voucher-list')


"""
class RangeUpdateView(UpdateView):
    model = Range
    template_name = 'dashboard/ranges/range_form.html'
    form_class = RangeForm

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
        messages.success(request, "%d product%s added to range" % (
            num_products, pluralize(num_products)))

        dupe_skus = form.get_duplicate_skus()
        if dupe_skus:
            messages.warning(
                request,
                "The products with SKUs or UPCs matching %s are already in this range" % (", ".join(dupe_skus)))

        missing_skus = form.get_missing_skus()
        if missing_skus:
            messages.warning(request,
                             "No product was found with SKU or UPC matching %s" % ', '.join(missing_skus))

    def handle_file_products(self, request, range, form):
        if not 'file_upload' in request.FILES:
            return 
        upload = self.create_upload_object(request, range)
        upload.process()
        if not upload.was_processing_successful():
            messages.error(request, upload.error_message)
        else:
            msg = "File processed: %d products added, %d duplicate identifiers, %d " \
                  "identifiers were not found"
            msg = msg % (upload.num_new_skus, upload.num_duplicate_skus,
                         upload.num_unknown_skus)
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
    """
