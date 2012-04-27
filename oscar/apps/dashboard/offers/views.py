from django.views.generic import ListView, FormView
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from oscar.core.loading import get_classes

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition= get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')
MetaDataForm, ConditionForm, BenefitForm, PreviewForm = get_classes('dashboard.offers.forms', [
    'MetaDataForm', 'ConditionForm', 'BenefitForm', 'PreviewForm'])


class OfferListView(ListView):
    model = ConditionalOffer
    context_object_name = 'offers'
    template_name = 'dashboard/offers/offer_list.html'


class OfferWizardStepView(FormView):
    wizard_name = 'offer_wizard'
    form_class = None
    step_name = None
    update = False
    url_name = None

    # Keep a reference to previous view class to allow checks to be made on whether
    # prior steps have been completed
    previous_view = None

    def dispatch(self, request, *args, **kwargs):
        if self.update:
            self.offer = get_object_or_404(ConditionalOffer, id=kwargs['pk'])
        if not self.is_previous_step_complete(request):
            messages.warning(request, "%s step not complete" %
                             self.previous_view.step_name.title())
            return HttpResponseRedirect(self.get_back_url())
        return super(OfferWizardStepView, self).dispatch(request, *args, **kwargs)

    def is_previous_step_complete(self, request):
        if not self.previous_view:
            return True
        return self.previous_view.is_valid(self, request)

    def _store_form_kwargs(self, form):
        session_data = self.request.session.setdefault(self.wizard_name, {})
        form_kwargs = {'data': form.cleaned_data.copy()}
        session_data[self.step_name] = form_kwargs
        self.request.session.save()

    def _fetch_form_kwargs(self, step_name=None):
        if not step_name:
            step_name = self.step_name
        session_data = self.request.session.setdefault(self.wizard_name, {})
        return session_data.get(step_name, {})

    def _store_object(self, form):
        session_data = self.request.session.setdefault(self.wizard_name, {})
        session_data[self.step_name + '_obj'] = form.save(commit=False)
        self.request.session.save()

    def _fetch_object(self, step_name, request=None):
        # We pass in the session as part of the checks on previous steps, as in those
        # cases we're using an
        if not request:
            request = self.request
        session_data = self.request.session.setdefault(self.wizard_name, {})
        return session_data.get(step_name + '_obj', None)

    def _flush_session(self):
        self.request.session[self.wizard_name] = {}
        self.request.session.save()

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = {}
        if self.update:
            form_kwargs['instance'] = self.get_instance()
        session_kwargs = self._fetch_form_kwargs()
        form_kwargs.update(session_kwargs)
        parent_kwargs = super(OfferWizardStepView, self).get_form_kwargs(*args, **kwargs)
        form_kwargs.update(parent_kwargs)
        return form_kwargs

    def get_context_data(self, **kwargs):
        ctx = super(OfferWizardStepView, self).get_context_data(**kwargs)
        if self.update:
            ctx['pk'] = self.kwargs.get('pk', None)
        ctx['back_url'] = self.get_back_url()
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
        if self.update:
            return "Edit %s for offer #%d" % (self.step_name, self.offer.id)
        return 'Create new offer: %s' % self.step_name

    def form_valid(self, form):
        self._store_form_kwargs(form)
        self._store_object(form)
        return super(OfferWizardStepView, self).form_valid(form)

    def get_success_url(self):
        if self.update:
            return reverse(self.success_url_name,
                           kwargs={'pk': self.kwargs['pk']})
        return reverse(self.success_url_name)

    @classmethod
    def is_valid(cls, current_view, request):
        if current_view.update:
            return True
        current_view.request = request
        return current_view._fetch_object(cls.step_name) is not None


class OfferMetaDataView(OfferWizardStepView):
    step_name = 'metadata'
    form_class = MetaDataForm
    template_name = 'dashboard/offers/metadata_form.html'
    url_name = 'dashboard:offer-metadata'
    success_url_name = 'dashboard:offer-condition'

    def get_instance(self):
        return self.offer


class OfferConditionView(OfferWizardStepView):
    step_name = 'condition'
    form_class = ConditionForm
    template_name = 'dashboard/offers/condition_form.html'
    url_name = 'dashboard:offer-condition'
    success_url_name = 'dashboard:offer-benefit'
    previous_view = OfferMetaDataView

    def get_instance(self):
        return self.offer.condition


class OfferBenefitView(OfferWizardStepView):
    step_name = 'benefit'
    form_class = BenefitForm
    template_name = 'dashboard/offers/benefit_form.html'
    url_name = 'dashboard:offer-benefit'
    success_url_name = 'dashboard:offer-preview'
    previous_view = OfferConditionView

    def get_instance(self):
        return self.offer.benefit


class OfferPreviewView(OfferWizardStepView):
    step_name = 'preview'
    form_class = PreviewForm
    template_name = 'dashboard/offers/preview.html'
    previous_view = OfferBenefitView
    url_name = 'dashboard:offer-preview'

    def get_context_data(self, **kwargs):
        ctx = super(OfferPreviewView, self).get_context_data(**kwargs)
        ctx['offer'] = self._fetch_object('metadata')
        ctx['condition'] = self._fetch_object('condition')
        ctx['benefit'] = self._fetch_object('benefit')
        return ctx

    def get_form_kwargs(self, *args, **kwargs):
        return super(OfferWizardStepView, self).get_form_kwargs(*args, **kwargs)

    def form_valid(self, form):
        condition = self._fetch_object('condition')
        condition.save()
        benefit = self._fetch_object('benefit')
        benefit.save()

        offer = self._fetch_object('metadata')
        offer.condition = condition
        offer.benefit = benefit
        offer.save()

        self._flush_session()

        if self.update:
            msg = "Offer #%d updated"
        else:
            msg = "Offer created!"
        messages.success(self.request, msg)

        return HttpResponseRedirect(self.get_success_url())

    def get_title(self):
        if self.update:
            return "Preview offer #%d" % self.offer.id
        return 'Preview offer'

    def get_success_url(self):
        return reverse('dashboard:offer-list')
