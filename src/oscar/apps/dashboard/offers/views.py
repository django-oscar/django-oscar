import json

from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, FormView, ListView

from oscar.core.loading import get_class, get_classes, get_model
from oscar.views import sort_queryset

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Range = get_model('offer', 'Range')
Product = get_model('catalogue', 'Product')
OrderDiscount = get_model('order', 'OrderDiscount')
Benefit = get_model('offer', 'Benefit')
MetaDataForm, ConditionForm, BenefitForm, RestrictionsForm, OfferSearchForm \
    = get_classes('dashboard.offers.forms',
                  ['MetaDataForm', 'ConditionForm', 'BenefitForm',
                   'RestrictionsForm', 'OfferSearchForm'])
OrderDiscountCSVFormatter = get_class(
    'dashboard.offers.reports', 'OrderDiscountCSVFormatter')


class OfferListView(ListView):
    model = ConditionalOffer
    context_object_name = 'offers'
    template_name = 'oscar/dashboard/offers/offer_list.html'
    form_class = OfferSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        self.search_filters = []
        qs = self.model._default_manager.all()
        qs = sort_queryset(qs, self.request, ['name', 'offer_type', 'start_datetime', 'end_datetime',
                                              'num_applications', 'total_discount'])

        self.form = self.form_class(self.request.GET)
        # This form is exactly the same as the other one, apart from having
        # fields with different IDs, so that they are unique within the page
        # (non-unique field IDs also break Select2)
        self.advanced_form = self.form_class(self.request.GET, auto_id='id_advanced_%s')
        if not all([self.form.is_valid(), self.advanced_form.is_valid()]):
            return qs

        name = self.form.cleaned_data['name']
        offer_type = self.form.cleaned_data['offer_type']
        is_active = self.form.cleaned_data['is_active']
        has_vouchers = self.form.cleaned_data['has_vouchers']
        voucher_code = self.form.cleaned_data['voucher_code']

        if name:
            qs = qs.filter(name__icontains=name)
            self.search_filters.append(_('Name matches "%s"') % name)
        if is_active is not None:
            now = timezone.now()
            if is_active:
                qs = qs.filter(
                    (Q(start_datetime__lte=now) | Q(start_datetime__isnull=True))
                    & (Q(end_datetime__gte=now) | Q(end_datetime__isnull=True))
                )
                self.search_filters.append(_("Is active"))
            else:
                qs = qs.filter(Q(end_datetime__lt=now) | Q(start_datetime__gt=now))
                self.search_filters.append(_("Is inactive"))
        if offer_type:
            qs = qs.filter(offer_type=offer_type)
            self.search_filters.append(_('Is of type "%s"') % dict(ConditionalOffer.TYPE_CHOICES)[offer_type])
        if has_vouchers is not None:
            qs = qs.filter(vouchers__isnull=not has_vouchers).distinct()
            self.search_filters.append(_("Has vouchers") if has_vouchers else _("Has no vouchers"))
        if voucher_code:
            qs = qs.filter(vouchers__code__icontains=voucher_code).distinct()
            self.search_filters.append(_('Voucher code matches "%s"') % voucher_code)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['advanced_form'] = self.advanced_form
        ctx['search_filters'] = self.search_filters
        return ctx


class OfferWizardStepView(FormView):
    wizard_name = 'offer_wizard'
    form_class = None
    step_name = None
    update = False
    url_name = None

    # Keep a reference to previous view class to allow checks to be made on
    # whether prior steps have been completed
    previous_view = None

    def dispatch(self, request, *args, **kwargs):
        if self.update:
            self.offer = get_object_or_404(ConditionalOffer, id=kwargs['pk'])
        if not self.is_previous_step_complete(request):
            messages.warning(
                request, _("%s step not complete") % (
                    self.previous_view.step_name.title(),))
            return HttpResponseRedirect(self.get_back_url())
        return super().dispatch(request, *args, **kwargs)

    def is_previous_step_complete(self, request):
        if not self.previous_view:
            return True
        return self.previous_view.is_valid(self, request)

    def _key(self, step_name=None, is_object=False):
        key = step_name if step_name else self.step_name
        if self.update:
            key += str(self.offer.id)
        if is_object:
            key += '_obj'
        return key

    def _store_form_kwargs(self, form):
        session_data = self.request.session.setdefault(self.wizard_name, {})

        # Adjust kwargs to avoid trying to save the range instance
        form_data = form.cleaned_data.copy()
        product_range = form_data.get('range')
        if product_range is not None:
            form_data['range'] = product_range.id

        combinations = form_data.get('combinations')
        if combinations is not None:
            form_data['combination_ids'] = [x.id for x in combinations]
            del form_data['combinations']

        form_kwargs = {'data': form_data}
        json_data = json.dumps(form_kwargs, cls=DjangoJSONEncoder)

        session_data[self._key()] = json_data
        self.request.session.save()

    def _fetch_form_kwargs(self):
        session_data = self.request.session.setdefault(self.wizard_name, {})
        json_data = session_data.get(self._key(self.step_name), None)
        if json_data:
            return json.loads(json_data)

        return {}

    def _store_object(self, form):
        session_data = self.request.session.setdefault(self.wizard_name, {})

        # We don't store the object instance as that is not JSON serialisable.
        # Instead, we save an alternative form
        instance = form.save(commit=False)
        # remove fields that do not exist (yet) on the uncommitted instance, i.e. m2m fields
        cleanfields = [field.name for field in instance._meta.local_fields]

        json_qs = serializers.serialize('json', [instance], fields=tuple(cleanfields))

        session_data[self._key(is_object=True)] = json_qs
        self.request.session.save()

    def _fetch_object(self, step_name, request=None):
        if request is None:
            request = self.request
        session_data = request.session.setdefault(self.wizard_name, {})
        json_qs = session_data.get(self._key(step_name, is_object=True), None)
        if json_qs:
            # Recreate model instance from passed data
            deserialised_obj = list(serializers.deserialize('json', json_qs))
            return deserialised_obj[0].object

    def _fetch_session_offer(self):
        """Return the offer instance loaded with the data stored in the session.

        When updating an offer, the updated fields are used with the existing
        offer data.
        """
        offer = self._fetch_object('metadata')
        if offer is None and self.update:
            offer = self.offer
        return offer

    def _flush_session(self):
        self.request.session[self.wizard_name] = {}
        self.request.session.save()

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = {}
        if self.update:
            form_kwargs['instance'] = self.get_instance()
        session_kwargs = self._fetch_form_kwargs()
        form_kwargs.update(session_kwargs)
        parent_kwargs = super().get_form_kwargs(
            *args, **kwargs)
        form_kwargs.update(parent_kwargs)
        return form_kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.update:
            ctx['offer'] = self.offer
        ctx['session_offer'] = self._fetch_session_offer()
        ctx['title'] = self.get_title()
        return ctx

    def get_back_url(self):
        if not self.previous_view:
            return None
        if self.update:
            return reverse(self.previous_view.url_name,
                           kwargs={'pk': self.kwargs['pk']})
        return reverse(self.previous_view.url_name)

    def get_title(self):
        return self.step_name.title()

    def form_valid(self, form):
        self._store_form_kwargs(form)
        self._store_object(form)

        if self.update and 'save' in form.data:
            # Save changes to this offer when updating and pressed save button
            return self.save_offer(self.offer)
        else:
            # Proceed to next page
            return super().form_valid(form)

    def save_offer(self, offer):
        # We update the offer with the name/description/offer_type from step 1
        session_offer = self._fetch_session_offer()
        offer.name = session_offer.name
        offer.description = session_offer.description
        offer.offer_type = session_offer.offer_type

        # Save the related models, then save the offer.
        # Note than you can save already on the first page of the wizard,
        # so le'ts check if the benefit and condition exist
        benefit = self._fetch_object('benefit')
        if benefit:
            benefit.save()
            offer.benefit = benefit

        condition = self._fetch_object('condition')
        if condition:
            condition.save()
            offer.condition = condition

        offer.save()

        self._flush_session()

        if self.update:
            msg = _("Offer '%s' updated") % offer.name
        else:
            msg = _("Offer '%s' created!") % offer.name
        messages.success(self.request, msg)

        return HttpResponseRedirect(reverse(
            'dashboard:offer-detail', kwargs={'pk': offer.pk}))

    def get_success_url(self):
        if self.update:
            return reverse(self.success_url_name,
                           kwargs={'pk': self.kwargs['pk']})
        return reverse(self.success_url_name)

    @classmethod
    def is_valid(cls, current_view, request):
        if current_view.update:
            return True
        return current_view._fetch_object(cls.step_name, request) is not None


class OfferMetaDataView(OfferWizardStepView):
    step_name = 'metadata'
    form_class = MetaDataForm
    template_name = 'oscar/dashboard/offers/metadata_form.html'
    url_name = 'dashboard:offer-metadata'
    success_url_name = 'dashboard:offer-benefit'

    def get_instance(self):
        return self.offer

    def get_title(self):
        return _("Name, description and type")


class OfferBenefitView(OfferWizardStepView):
    step_name = 'benefit'
    form_class = BenefitForm
    template_name = 'oscar/dashboard/offers/benefit_form.html'
    url_name = 'dashboard:offer-benefit'
    success_url_name = 'dashboard:offer-condition'
    previous_view = OfferMetaDataView

    def get_instance(self):
        return self.offer.benefit

    def get_title(self):
        # This is referred to as the 'incentive' within the dashboard.
        return _("Incentive")


class OfferConditionView(OfferWizardStepView):
    step_name = 'condition'
    form_class = ConditionForm
    template_name = 'oscar/dashboard/offers/condition_form.html'
    url_name = 'dashboard:offer-condition'
    success_url_name = 'dashboard:offer-restrictions'
    previous_view = OfferBenefitView

    def get_instance(self):
        return self.offer.condition


class OfferRestrictionsView(OfferWizardStepView):
    step_name = 'restrictions'
    form_class = RestrictionsForm
    template_name = 'oscar/dashboard/offers/restrictions_form.html'
    previous_view = OfferConditionView
    url_name = 'dashboard:offer-restrictions'

    def form_valid(self, form):
        offer = form.save(commit=False)
        return self.save_offer(offer)

    def get_instance(self):
        return self.offer

    def get_title(self):
        return _("Restrictions")


class OfferDeleteView(DeleteView):
    model = ConditionalOffer
    template_name = 'oscar/dashboard/offers/offer_delete.html'
    context_object_name = 'offer'

    def dispatch(self, request, *args, **kwargs):
        offer = self.get_object()
        if offer.vouchers.exists():
            messages.warning(request, _("This offer can only be deleted if it has no vouchers attached to it"))
            return redirect('dashboard:offer-detail', pk=offer.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, _("Offer deleted!"))
        return reverse('dashboard:offer-list')


class OfferDetailView(ListView):
    # Slightly odd, but we treat the offer detail view as a list view so the
    # order discounts can be browsed.
    model = OrderDiscount
    template_name = 'oscar/dashboard/offers/offer_detail.html'
    context_object_name = 'order_discounts'
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def dispatch(self, request, *args, **kwargs):
        self.offer = get_object_or_404(ConditionalOffer, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'suspend' in request.POST:
            return self.suspend()
        elif 'unsuspend' in request.POST:
            return self.unsuspend()

    def suspend(self):
        if self.offer.is_suspended:
            messages.error(self.request, _("Offer is already suspended"))
        else:
            self.offer.suspend()
            messages.success(self.request, _("Offer suspended"))
        return HttpResponseRedirect(
            reverse('dashboard:offer-detail', kwargs={'pk': self.offer.pk}))

    def unsuspend(self):
        if not self.offer.is_suspended:
            messages.error(
                self.request,
                _("Offer cannot be reinstated as it is not currently "
                  "suspended"))
        else:
            self.offer.unsuspend()
            messages.success(self.request, _("Offer reinstated"))
        return HttpResponseRedirect(
            reverse('dashboard:offer-detail', kwargs={'pk': self.offer.pk}))

    def get_queryset(self):
        return self.model.objects.filter(offer_id=self.offer.pk) \
            .select_related('order')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['offer'] = self.offer
        return ctx

    def render_to_response(self, context):
        if self.request.GET.get('format') == 'csv':
            formatter = OrderDiscountCSVFormatter()
            return formatter.generate_response(context['order_discounts'],
                                               offer=self.offer)
        return super().render_to_response(context)
