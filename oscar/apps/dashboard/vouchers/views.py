import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (ListView, FormView, DetailView, DeleteView)

from oscar.core.loading import get_class
from oscar.views import sort_queryset

VoucherForm = get_class('dashboard.vouchers.forms', 'VoucherForm')
VoucherSearchForm = get_class('dashboard.vouchers.forms', 'VoucherSearchForm')
Voucher = get_model('voucher', 'Voucher')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Benefit = get_model('offer', 'Benefit')
Condition = get_model('offer', 'Condition')
OrderDiscount = get_model('order', 'OrderDiscount')


class VoucherListView(ListView):
    model = Voucher
    context_object_name = 'vouchers'
    template_name = 'dashboard/vouchers/voucher_list.html'
    form_class = VoucherSearchForm
    description_template = _("%(main_filter)s %(name_filter)s %(code_filter)s")

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
        if 'name' not in self.request.GET:
            self.form = self.form_class()
            return qs

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
            today = datetime.date.today()
            qs = qs.filter(start_date__lte=today, end_date__gte=today)
            self.description_ctx['main_filter'] = _('Active vouchers')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super(VoucherListView, self).get_context_data(**kwargs)
        ctx['description'] = self.description_template % self.description_ctx
        ctx['form'] = self.form
        return ctx


class VoucherCreateView(FormView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_form.html'
    form_class = VoucherForm

    def get_context_data(self, **kwargs):
        ctx = super(VoucherCreateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Create voucher')
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
            name=_("Offer for voucher '%s'") % name,
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
        messages.success(self.request, _("Voucher created"))
        return reverse('dashboard:voucher-list')


class VoucherStatsView(DetailView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_detail.html'
    context_object_name = 'voucher'

    def get_context_data(self, **kwargs):
        ctx = super(VoucherStatsView, self).get_context_data(**kwargs)
        discounts = OrderDiscount.objects.filter(voucher_id=self.object.id)
        discounts = discounts.order_by('-order__date_placed')
        ctx['discounts'] = discounts
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
        ctx['title'] = _('Update voucher')
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
        messages.success(self.request, _("Voucher updated"))
        return reverse('dashboard:voucher-list')


class VoucherDeleteView(DeleteView):
    model = Voucher
    template_name = 'dashboard/vouchers/voucher_delete.html'
    context_object_name = 'voucher'

    def get_success_url(self):
        messages.warning(self.request, _("Voucher deleted"))
        return reverse('dashboard:voucher-list')
