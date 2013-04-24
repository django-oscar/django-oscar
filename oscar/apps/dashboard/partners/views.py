from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from oscar.core.loading import get_classes
from oscar.views.generic import BulkEditMixin

Partner = get_model('partner', 'Partner')
PartnerSearchForm, PartnerCreateForm = get_classes('dashboard.partners.forms', ['PartnerSearchForm', 'PartnerCreateForm'])


class PartnerListView(generic.ListView, BulkEditMixin):
    model = Partner
    context_object_name = 'partners'
    template_name = 'dashboard/partners/partner_list.html'
    form_class = PartnerSearchForm

    def get_queryset(self):
        qs = self.model._default_manager.all()
        qs = self.sort_queryset(qs)

        self.description = _("All partners")

        # We track whether the queryset is filtered to determine whether we
        # show the search form 'reset' button.
        self.is_filtered = False
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs

        data = self.form.cleaned_data

        if data['name']:
            qs = qs.filter(name__icontains=data['name'])
            self.description = _("Partners matching '%s'") % data['name']
            self.is_filtered = True

        return qs

    def sort_queryset(self, queryset):
        sort = self.request.GET.get('sort', None)
        allowed_sorts = ['name']
        if sort in allowed_sorts:
            direction = self.request.GET.get('dir', 'desc')
            sort = ('-' if direction == 'desc' else '') + sort
            queryset = queryset.order_by(sort)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super(PartnerListView, self).get_context_data(**kwargs)
        ctx['queryset_description'] = self.description
        ctx['form'] = self.form
        ctx['is_filtered'] = self.is_filtered
        return ctx


class PartnerCreateView(generic.CreateView):
    model = Partner
    template_name = 'dashboard/partners/partner_form.html'
    form_class = PartnerCreateForm
    success_url = reverse_lazy('dashboard:partner-list')


class PartnerUpdateView(generic.UpdateView):
    model = Partner
    template_name = 'dashboard/partners/partner_form.html'
    form_class = PartnerCreateForm

    def get_success_url(self):
        messages.success(self.request,
                         _("Partner '%s' was updated successfully.") %
                         self.object.name)
        return reverse_lazy('dashboard:partner-list')


class PartnerDeleteView(generic.DeleteView):
    model = Partner
    template_name = 'dashboard/partners/partner_delete.html'

    def get_success_url(self):
        messages.success(self.request,
                         _("Partner '%s' was deleted successfully.") %
                         self.object.name)
        return reverse_lazy('dashboard:partner-list')

