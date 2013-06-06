from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import get_model
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.views import generic

from oscar.apps.dashboard.partners.forms import UserEmailForm, ExistingUserForm, NewUserForm
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


class PartnerManageView(generic.UpdateView):
    """
    Is a merge of an UpdateView to update the name of the partner,
    and a ListView to list associated users.
    """
    model = Partner
    template_name = 'dashboard/partners/partner_manage.html'
    form_class = PartnerCreateForm
    context_object_name = 'partner'

    def get_context_data(self, **kwargs):
        ctx = super(PartnerManageView, self).get_context_data(**kwargs)
        ctx['title'] = self.object.name
        ctx['users'] = self.object.users.all()
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


class PartnerUserCreateView(generic.CreateView):
    model = User
    template_name = 'dashboard/partners/partner_user_form.html'
    form_class = NewUserForm

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(
            Partner, pk=kwargs.get('partner_pk', None))
        return super(PartnerUserCreateView, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PartnerUserCreateView, self).get_context_data(**kwargs)
        ctx['partner'] = self.partner
        ctx['title'] = _('Create user')
        return ctx

    def get_form_kwargs(self):
        kwargs = super(PartnerUserCreateView, self).get_form_kwargs()
        kwargs['partner'] = self.partner
        return kwargs

    def get_success_url(self):
        name = self.object.get_full_name() or self.object.email
        messages.success(self.request,
                         _("User '%s' was created successfully.") % name)
        return reverse_lazy('dashboard:partner-list')


class PartnerUserSelectView(generic.ListView):
    template_name = 'dashboard/partners/partner_user_select.html'
    form_class = UserEmailForm
    context_object_name = 'users'

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(
            Partner, pk=kwargs.get('partner_pk', None))
        return super(PartnerUserSelectView, self).dispatch(
            request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        data = None
        if 'email' in request.GET:
            data = request.GET
        self.form = self.form_class(data)
        return super(PartnerUserSelectView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PartnerUserSelectView, self).get_context_data(**kwargs)
        ctx['partner'] = self.partner
        ctx['form'] = self.form
        return ctx

    def get_queryset(self):
        if self.form.is_valid():
            email = self.form.cleaned_data['email']
            return User.objects.filter(is_staff=True, email__icontains=email)
        else:
            return User.objects.none()


class PartnerUserLinkView(generic.View):

    def get(self, request, user_pk, partner_pk):
        # need to allow GET to make Undo link in PartnerUserUnlinkView work
        return self.post(request, user_pk, partner_pk)

    def post(self, request, user_pk, partner_pk):
        user = get_object_or_404(User, pk=user_pk)
        partner = get_object_or_404(Partner, pk=partner_pk)
        name = user.get_full_name() or user.email
        if not partner.users.filter(pk=user_pk).exists():
            partner.users.add(user)
            messages.success(
                request, _("User '%(name)s' was linked to '%(partner_name)s'") %
                {'name': name, 'partner_name': partner.name})
        else:
            messages.error(
                request, _("User '%(name)s' is already linked to '%(partner_name)s'") %
                {'name': name, 'partner_name': partner.name})
        return HttpResponseRedirect(reverse('dashboard:partner-manage',
                                            kwargs={'pk': partner_pk}))


class PartnerUserUnlinkView(generic.View):

    def post(self, request, user_pk, partner_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.email
        partner = get_object_or_404(Partner, pk=partner_pk)
        if partner.users.filter(pk=user_pk).exists():
            partner.users.remove(user)
            msg = render_to_string(
                'dashboard/partners/messages/user_unlinked.html',
                {'user_name': name,
                 'partner_name': partner.name,
                 'user_pk': user_pk,
                 'partner_pk': partner_pk })
            messages.success(self.request, msg, extra_tags='safe')
        else:
            messages.error(
                request, _("User '%(name)s' is not linked to '%(partner_name)s'") %
                {'name': name, 'partner_name': partner.name})
        return HttpResponseRedirect(reverse('dashboard:partner-manage',
                                            kwargs={'pk': partner_pk}))


# =====
# Users
# =====


class PartnerUserUpdateView(generic.UpdateView):
    template_name = 'dashboard/partners/partner_user_form.html'
    form_class = ExistingUserForm

    def get_object(self, queryset=None):
        return get_object_or_404(User,
                                 pk=self.kwargs['user_pk'],
                                 partners__pk=self.kwargs['partner_pk'],
                                 is_staff=True)

    def get_context_data(self, **kwargs):
        ctx = super(PartnerUserUpdateView, self).get_context_data(**kwargs)
        name = self.object.get_full_name() or self.object.email
        ctx['title'] = _("Edit user '%s'") % name
        return ctx

    def get_success_url(self):
        name = self.object.get_full_name() or self.object.email
        messages.success(self.request,
                         _("User '%s' was updated successfully.") % name)
        return reverse_lazy('dashboard:partner-list')


