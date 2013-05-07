from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import get_model
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from oscar.apps.dashboard.partners.forms import UserForm
from oscar.core.loading import get_classes
from oscar.views.generic import BulkEditMixin

Partner = get_model('partner', 'Partner')
PartnerSearchForm, PartnerCreateForm = get_classes(
    'dashboard.partners.forms', ['PartnerSearchForm', 'PartnerCreateForm'])


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

    def get_context_data(self, **kwargs):
        ctx = super(PartnerCreateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Create new partner')
        return ctx

    def get_success_url(self):
        messages.success(self.request,
                         _("Partner '%s' was created successfully.") %
                         self.object.name)
        return reverse_lazy('dashboard:partner-list')


class PartnerUpdateView(generic.UpdateView):
    model = Partner
    template_name = 'dashboard/partners/partner_form.html'
    form_class = PartnerCreateForm
    context_object_name = 'partner'

    def get_context_data(self, **kwargs):
        ctx = super(PartnerUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = self.object.name
        return ctx

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


# =============
# Partner users
# =============


class PartnerCreateUserView(generic.CreateView):
    model = User
    template_name = 'dashboard/partners/partner_user_form.html'
    form_class = UserForm

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(
            Partner, pk=kwargs.get('partner_pk', None))
        return super(PartnerCreateUserView, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PartnerCreateUserView, self).get_context_data(**kwargs)
        ctx['partner'] = self.partner
        return ctx

    def form_valid(self, form):
        ret = super(PartnerCreateUserView, self).form_valid(form)
        self.partner.users.add(self.object)
        return ret

    def get_success_url(self):
        name = self.object.get_full_name() or self.object.email
        messages.success(self.request,
                         _("User '%s' was created successfully.") % name)
        return reverse_lazy('dashboard:partner-list')


class PartnerUpdateUserView(generic.UpdateView):
    model = User
    template_name = 'dashboard/partners/partner_user_form.html'
    form_class = UserForm

    def get_context_data(self, **kwargs):
        name = self.object.get_full_name() or self.object.email
        ctx = super(PartnerUpdateUserView, self).get_context_data(**kwargs)
        ctx['title'] = _("Edit user '%s'") % name
        return ctx

    def get_success_url(self):
        name = self.object.get_full_name() or self.object.email
        messages.success(self.request,
                         _("User '%s' was updated successfully.") % name)
        return reverse_lazy('dashboard:partner-list')


class PartnerManageUsers(generic.ListView):
    model = User
    template_name = 'dashboard/partners/manage_users.html'
    context_object_name = 'users'

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(
            Partner, pk=kwargs.get('pk', None))
        return super(PartnerManageUsers, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PartnerManageUsers, self).get_context_data(**kwargs)
        ctx['partner'] = self.partner
        return ctx

    def get_queryset(self):
        return self.partner.users.all()


class PartnerUnlinkUserView(generic.View):

    def post(self, request, user_pk, partner_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.email
        partner = get_object_or_404(Partner, pk=partner_pk)
        users = partner.users.all()
        if user in users:
            partner.users.remove(user)
            messages.success(request, _("User '%s' was unlinked from '%s'") %
                                      (name, partner.name))
        else:
            messages.error(request, _("User '%s' is not linked to '%s'") %
                                    (name, partner.name))
        return HttpResponseRedirect(reverse('dashboard:partner-manage-users',
                                            kwargs={'pk': partner_pk}))


