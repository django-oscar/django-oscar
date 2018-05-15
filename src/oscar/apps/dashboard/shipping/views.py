from django import shortcuts
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import generic

from oscar.core.loading import get_classes, get_model

WeightBandForm, WeightBasedForm = get_classes(
    'dashboard.shipping.forms', ['WeightBandForm', 'WeightBasedForm'])
WeightBased = get_model('shipping', 'WeightBased')
WeightBand = get_model('shipping', 'WeightBand')


class WeightBasedListView(generic.ListView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_list.html"
    context_object_name = "methods"


class WeightBasedCreateView(generic.CreateView):
    model = WeightBased
    form_class = WeightBasedForm
    template_name = "dashboard/shipping/weight_based_form.html"

    def get_success_url(self):
        msg = render_to_string(
            'dashboard/shipping/messages/method_created.html',
            {'method': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:shipping-method-detail',
                       kwargs={'pk': self.object.pk})


class WeightBasedDetailView(generic.CreateView):
    model = WeightBand
    form_class = WeightBandForm
    template_name = "dashboard/shipping/weight_based_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.method = shortcuts.get_object_or_404(
            WeightBased, pk=kwargs['pk'])
        return super(WeightBasedDetailView, self).dispatch(
            request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(WeightBasedDetailView, self).get_form_kwargs(**kwargs)
        kwargs['method'] = self.method
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(WeightBasedDetailView, self).get_context_data(**kwargs)
        ctx['method'] = self.method
        return ctx

    def get_success_url(self):
        msg = render_to_string(
            'dashboard/shipping/messages/band_created.html',
            {'band': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:shipping-method-detail',
                       kwargs={'pk': self.method.pk})


class WeightBasedUpdateView(generic.UpdateView):
    model = WeightBased
    form_class = WeightBasedForm
    template_name = "dashboard/shipping/weight_based_form.html"
    context_object_name = "method"

    def get_success_url(self):
        msg = render_to_string(
            'dashboard/shipping/messages/method_updated.html',
            {'method': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:shipping-method-detail',
                       kwargs={'pk': self.object.pk})


class WeightBandUpdateView(generic.UpdateView):
    model = WeightBand
    form_class = WeightBandForm
    template_name = "dashboard/shipping/weight_band_form.html"
    context_object_name = "band"

    def dispatch(self, request, *args, **kwargs):
        self.method = shortcuts.get_object_or_404(
            WeightBased, pk=kwargs['method_pk'])
        return super(WeightBandUpdateView, self).dispatch(
            request, *args, **kwargs)

    def get_queryset(self):
        return self.method.bands.all()

    def get_form_kwargs(self, **kwargs):
        kwargs = super(WeightBandUpdateView, self).get_form_kwargs(**kwargs)
        kwargs['method'] = self.method
        return kwargs

    def get_success_url(self):
        msg = render_to_string(
            'dashboard/shipping/messages/band_updated.html',
            {'band': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:shipping-method-detail',
                       kwargs={'pk': self.method.pk})


class WeightBandDeleteView(generic.DeleteView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_band_delete.html"
    context_object_name = "band"

    def dispatch(self, request, *args, **kwargs):
        self.method = shortcuts.get_object_or_404(
            WeightBased, pk=kwargs['method_pk'])
        return super(WeightBandDeleteView, self).dispatch(
            request, *args, **kwargs)

    def get_queryset(self):
        return self.method.bands.all()

    def get_success_url(self):
        msg = render_to_string(
            'dashboard/shipping/messages/band_deleted.html',
            {'band': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:shipping-method-detail',
                       kwargs={'pk': self.method.pk})


class WeightBasedDeleteView(generic.DeleteView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_delete.html"
    context_object_name = "method"

    def get_success_url(self):
        msg = render_to_string(
            'dashboard/shipping/messages/method_deleted.html',
            {'method': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:shipping-method-list')
