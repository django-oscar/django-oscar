from django.views import generic
from django import shortcuts
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model, get_class

WeightBandForm = get_class('dashboard.shipping.forms', 'WeightBandForm')
WeightBased = get_model('shipping', 'WeightBased')
WeightBand = get_model('shipping', 'WeightBand')


class WeightBasedListView(generic.ListView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_list.html"
    context_object_name = "methods"


class WeightBasedCreateView(generic.CreateView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_form.html"

    def get_success_url(self):
        messages.success(self.request, _("Shipping method created"))
        return reverse('dashboard:shipping-method-list')


class WeightBasedDetailView(generic.CreateView):
    model = WeightBand
    template_name = "dashboard/shipping/weight_based_detail.html"
    form_class = WeightBandForm

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
        messages.success(self.request, _("Shipping band created"))
        return reverse('dashboard:shipping-method-detail',
                       kwargs={'pk': self.method.pk})


class WeightBasedUpdateView(generic.UpdateView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_form.html"
    context_object_name = "method"

    def get_success_url(self):
        messages.success(self.request, _("Shipping method updated"))
        return reverse('dashboard:shipping-method-list')


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
        messages.success(self.request, _("Weight band updated"))
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
        messages.success(self.request, _("Weight band deleted"))
        return reverse('dashboard:shipping-method-detail',
                       kwargs={'pk': self.method.pk})


class WeightBasedDeleteView(generic.DeleteView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_delete.html"
    context_object_name = "method"

    def get_success_url(self):
        messages.success(self.request, _("Shipping method deleted"))
        return reverse('dashboard:shipping-method-list')
