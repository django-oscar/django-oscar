import csv

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from oscar.core.loading import get_class, get_model
from oscar.core.utils import slugify
from oscar.views import sort_queryset

VoucherForm = get_class('dashboard.vouchers.forms', 'VoucherForm')
VoucherSetForm = get_class('dashboard.vouchers.forms', 'VoucherSetForm')
VoucherSetSearchForm = get_class('dashboard.vouchers.forms', 'VoucherSetSearchForm')
VoucherSearchForm = get_class('dashboard.vouchers.forms', 'VoucherSearchForm')
Voucher = get_model('voucher', 'Voucher')
VoucherSet = get_model('voucher', 'VoucherSet')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Benefit = get_model('offer', 'Benefit')
Condition = get_model('offer', 'Condition')
OrderDiscount = get_model('order', 'OrderDiscount')


class VoucherListView(generic.ListView):
    model = Voucher
    context_object_name = 'vouchers'
    template_name = 'dashboard/vouchers/voucher_list.html'
    form_class = VoucherSearchForm
    description_template = _("%(main_filter)s %(name_filter)s %(code_filter)s")
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        qs = self.model.objects.all().order_by('-date_created')
        qs = sort_queryset(qs, self.request,
                           ['num_basket_additions', 'num_orders',
                            'date_created'],
                           '-date_created')
        self.description_ctx = {'main_filter': _('All vouchers'),
                                'name_filter': '',
                                'code_filter': ''}

        # If form not submitted, return early
        is_form_submitted = 'name' in self.request.GET
        if not is_form_submitted:
            self.form = self.form_class()
            return qs.filter(voucher_set__isnull=True)

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs

        data = self.form.cleaned_data
        if data['name']:
            qs = qs.filter(name__icontains=data['name'])
            self.description_ctx['name_filter'] \
                = _("with name matching '%s'") % data['name']
        if data['code']:
            qs = qs.filter(code=data['code'])
            self.description_ctx['code_filter'] \
                = _("with code '%s'") % data['code']
        if data['is_active']:
            now = timezone.now()
            qs = qs.filter(start_datetime__lte=now, end_datetime__gte=now)
            self.description_ctx['main_filter'] = _('Active vouchers')
        if not data['in_set']:
            qs = qs.filter(voucher_set__isnull=True)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.form.is_bound:
            description = self.description_template % self.description_ctx
        else:
            description = _("Vouchers")
        ctx['description'] = description
        ctx['form'] = self.form
        return ctx


class VoucherCreateView(generic.FormView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_form.html'
    form_class = VoucherForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _('Create voucher')
        return ctx

    def get_initial(self):
        return dict(
            exclusive=True
        )

    @transaction.atomic()
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
            name=_("Offer for voucher '%s'") % name,
            offer_type=ConditionalOffer.VOUCHER,
            benefit=benefit,
            condition=condition,
            exclusive=form.cleaned_data['exclusive'],
        )
        voucher = Voucher.objects.create(
            name=name,
            code=form.cleaned_data['code'],
            usage=form.cleaned_data['usage'],
            start_datetime=form.cleaned_data['start_datetime'],
            end_datetime=form.cleaned_data['end_datetime'],
        )
        voucher.offers.add(offer)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, _("Voucher created"))
        return reverse('dashboard:voucher-list')


class VoucherStatsView(generic.DetailView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_detail.html'
    context_object_name = 'voucher'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        discounts = OrderDiscount.objects.filter(voucher_id=self.object.id)
        discounts = discounts.order_by('-order__date_placed')
        ctx['discounts'] = discounts
        return ctx


class VoucherUpdateView(generic.FormView):
    template_name = 'dashboard/vouchers/voucher_form.html'
    model = Voucher
    form_class = VoucherForm

    def get_voucher(self):
        if not hasattr(self, 'voucher'):
            self.voucher = Voucher.objects.get(id=self.kwargs['pk'])
        return self.voucher

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.voucher.name
        ctx['voucher'] = self.voucher
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['voucher'] = self.get_voucher()
        return kwargs

    def get_initial(self):
        voucher = self.get_voucher()
        offer = voucher.offers.all()[0]
        benefit = offer.benefit
        return {
            'name': voucher.name,
            'code': voucher.code,
            'start_datetime': voucher.start_datetime,
            'end_datetime': voucher.end_datetime,
            'usage': voucher.usage,
            'benefit_type': benefit.type,
            'benefit_range': benefit.range,
            'benefit_value': benefit.value,
            'exclusive': offer.exclusive,
        }

    @transaction.atomic()
    def form_valid(self, form):
        voucher = self.get_voucher()
        voucher.name = form.cleaned_data['name']
        voucher.code = form.cleaned_data['code']
        voucher.usage = form.cleaned_data['usage']
        voucher.start_datetime = form.cleaned_data['start_datetime']
        voucher.end_datetime = form.cleaned_data['end_datetime']
        voucher.save()

        offer = voucher.offers.all()[0]
        offer.condition.range = form.cleaned_data['benefit_range']
        offer.condition.save()

        offer.exclusive = form.cleaned_data['exclusive']
        offer.save()

        benefit = voucher.benefit
        benefit.range = form.cleaned_data['benefit_range']
        benefit.type = form.cleaned_data['benefit_type']
        benefit.value = form.cleaned_data['benefit_value']
        benefit.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, _("Voucher updated"))
        return reverse('dashboard:voucher-list')


class VoucherDeleteView(generic.DeleteView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_delete.html'
    context_object_name = 'voucher'

    def get_success_url(self):
        messages.warning(self.request, _("Voucher deleted"))
        return reverse('dashboard:voucher-list')


class VoucherSetCreateView(generic.CreateView):
    model = VoucherSet
    template_name = 'dashboard/vouchers/voucher_set_form.html'
    form_class = VoucherSetForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _('Create voucher set')
        return ctx

    def get_initial(self):
        return {
            'start_datetime': timezone.now(),
            'end_datetime': timezone.now()
        }

    def form_valid(self, form):
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
            name=_("Offer for voucher '%s'") % name,
            offer_type=ConditionalOffer.VOUCHER,
            benefit=benefit,
            condition=condition,
        )

        VoucherSet.objects.create(
            name=name,
            count=form.cleaned_data['count'],
            code_length=form.cleaned_data['code_length'],
            description=form.cleaned_data['description'],
            start_datetime=form.cleaned_data['start_datetime'],
            end_datetime=form.cleaned_data['end_datetime'],
            offer=offer,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, _("Voucher set created"))
        return reverse('dashboard:voucher-set-list')


class VoucherSetUpdateView(generic.UpdateView):
    template_name = 'dashboard/vouchers/voucher_set_form.html'
    model = VoucherSet
    form_class = VoucherSetForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.object.name
        ctx['voucher'] = self.object
        return ctx

    def get_voucherset(self):
        if not hasattr(self, 'voucherset'):
            self.voucherset = VoucherSet.objects.get(id=self.kwargs['pk'])
        return self.voucherset

    def get_initial(self):
        voucherset = self.get_voucherset()
        offer = voucherset.offer
        benefit = offer.benefit
        return {
            'name': voucherset.name,
            'count': voucherset.count,
            'code_length': voucherset.code_length,
            'start_datetime': voucherset.start_datetime,
            'end_datetime': voucherset.end_datetime,
            'description': voucherset.description,
            'benefit_type': benefit.type,
            'benefit_range': benefit.range,
            'benefit_value': benefit.value,
        }

    def form_valid(self, form):
        voucherset = form.save()
        if not voucherset.offer:
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
            offer, __ = ConditionalOffer.objects.update_or_create(
                name=_("Offer for voucher '%s'") % name,
                defaults=dict(
                    offer_type=ConditionalOffer.VOUCHER,
                    benefit=benefit,
                    condition=condition,
                )
            )
            voucherset.offer = offer
            for voucher in voucherset.vouchers.all():
                if offer not in voucher.offers.all():
                    voucher.offers.add(offer)

        else:
            benefit = voucherset.offer.benefit
            benefit.range = form.cleaned_data['benefit_range']
            benefit.type = form.cleaned_data['benefit_type']
            benefit.value = form.cleaned_data['benefit_value']
            benefit.save()
            condition = voucherset.offer.condition
            condition.range = form.cleaned_data['benefit_range']
            condition.save()
        voucherset.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, _("Voucher updated"))
        return reverse('dashboard:voucher-set', kwargs={'pk': self.object.pk})


class VoucherSetDetailView(generic.ListView):

    model = Voucher
    context_object_name = 'vouchers'
    template_name = 'dashboard/vouchers/voucher_set_detail.html'
    form_class = VoucherSetSearchForm
    description_template = _("%(main_filter)s %(name_filter)s %(code_filter)s")
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.voucher_set = get_object_or_404(VoucherSet, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = (
            self.model.objects
            .filter(voucher_set=self.voucher_set)
            .order_by('-date_created'))

        qs = sort_queryset(qs, self.request,
                           ['num_basket_additions', 'num_orders',
                            'date_created'],
                           '-date_created')
        self.description_ctx = {'main_filter': _('All vouchers'),
                                'name_filter': '',
                                'code_filter': ''}

        # If form not submitted, return early
        is_form_submitted = (
            'name' in self.request.GET or 'code' in self.request.GET
        )
        if not is_form_submitted:
            self.form = self.form_class()
            return qs

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs

        data = self.form.cleaned_data
        if data['code']:
            qs = qs.filter(code__icontains=data['code'])
            self.description_ctx['code_filter'] \
                = _("with code '%s'") % data['code']
        if data['is_active']:
            now = timezone.now()
            qs = qs.filter(start_datetime__lte=now, end_datetime__gt=now)
            self.description_ctx['main_filter'] = _('Active vouchers')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['voucher_set'] = self.voucher_set
        ctx['description'] = self.voucher_set.name
        ctx['form'] = self.form
        return ctx


class VoucherSetListView(generic.ListView):
    model = VoucherSet
    context_object_name = 'vouchers'
    template_name = 'dashboard/vouchers/voucher_set_list.html'
    description_template = _("%(main_filter)s %(name_filter)s %(code_filter)s")
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        qs = self.model.objects.all().order_by('-date_created')
        qs = sort_queryset(
            qs, self.request,
            ['num_basket_additions', 'num_orders', 'date_created'], '-date_created')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        description = _("Voucher sets")
        ctx['description'] = description
        return ctx


class VoucherSetDownloadView(generic.DetailView):
    template_name = 'dashboard/vouchers/voucher_set_form.html'
    model = VoucherSet
    form_class = VoucherSetForm

    def get(self, request, *args, **kwargs):
        voucher_set = self.get_object()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="%s.csv"' % slugify(voucher_set.name))

        writer = csv.writer(response)
        for code in voucher_set.vouchers.values_list('code', flat=True):
            writer.writerow([code])

        return response
