from django.views.generic import ListView, FormView
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

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

    def _fetch_object(self, step_name):
        session_data = self.request.session.setdefault(self.wizard_name, {})
        return session_data[step_name + '_obj']

    def _flush_session(self):
        self.request.session[self.wizard_name] = {}
        self.request.session.save()

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = {}
        if self.update and hasattr(self.form_class, '_meta'):
            model = self.form_class._meta.model
            obj = model._default_manager.get(id=self.kwargs['pk'])
            form_kwargs['instance'] = obj
        session_kwargs = self._fetch_form_kwargs()
        form_kwargs.update(session_kwargs)
        parent_kwargs = super(OfferWizardStepView, self).get_form_kwargs(*args, **kwargs)
        form_kwargs.update(parent_kwargs)
        return form_kwargs

    def get_context_data(self, **kwargs):
        ctx = super(OfferWizardStepView, self).get_context_data(**kwargs)
        ctx['pk'] = self.kwargs.get('pk', None)
        return ctx

    def form_valid(self, form):
        self._store_form_kwargs(form)
        self._store_object(form)
        return super(OfferWizardStepView, self).form_valid(form)

    def get_success_url(self):
        if self.update:
            return reverse(self.url_name,
                           kwargs={'pk': self.kwargs['pk']})
        return reverse(self.url_name)


class OfferMetaDataView(OfferWizardStepView):
    step_name = 'metadata'
    form_class = MetaDataForm
    template_name = 'dashboard/offers/metadata_form.html'
    url_name = 'dashboard:offer-condition'


class OfferConditionView(OfferWizardStepView):
    step_name = 'condition'
    form_class = ConditionForm
    template_name = 'dashboard/offers/condition_form.html'
    url_name = 'dashboard:offer-benefit'


class OfferBenefitView(OfferWizardStepView):
    step_name = 'benefit'
    form_class = BenefitForm
    template_name = 'dashboard/offers/benefit_form.html'
    url_name = 'dashboard:offer-preview'


class OfferPreviewView(OfferWizardStepView):
    step_name = 'preview'
    form_class = PreviewForm
    template_name = 'dashboard/offers/preview.html'

    def get_context_data(self, **kwargs):
        ctx = super(OfferPreviewView, self).get_context_data(**kwargs)
        ctx['offer'] = self._fetch_object('metadata')
        ctx['condition'] = self._fetch_object('condition')
        ctx['benefit'] = self._fetch_object('benefit')
        return ctx

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

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('dashboard:offer-list')
