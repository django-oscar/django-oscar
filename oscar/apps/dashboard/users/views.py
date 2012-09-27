from django.db.models import Q, get_model
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic import ListView, DetailView, DeleteView, UpdateView

from oscar.views.generic import BulkEditMixin
from oscar.core.loading import get_classes

UserSearchForm, ProductAlertSearchForm, ProductAlertUpdateForm  = get_classes(
    'dashboard.users.forms', ('UserSearchForm', 'ProductAlertSearchForm',
                              'ProductAlertUpdateForm'))
ProductAlert = get_model('customer', 'ProductAlert')


class IndexView(ListView, BulkEditMixin):
    template_name = 'dashboard/users/index.html'
    paginate_by = 25
    model = User
    actions = ('make_active', 'make_inactive', )
    current_view = 'dashboard:users-index'
    form_class = UserSearchForm
    desc_template = _('%(main_filter)s %(email_filter)s %(name_filter)s')
    description = ''

    def get_queryset(self):
        queryset = self.model.objects.all().order_by('-date_joined')
        self.desc_ctx = {
            'main_filter': _('All users'),
            'email_filter': '',
            'name_filter': '',
        }

        if 'email' not in self.request.GET:
            self.form = self.form_class()
            return queryset

        self.form = self.form_class(self.request.GET)

        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['email']:
            queryset = queryset.filter(email__startswith=data['email'])
            self.desc_ctx['email_filter'] = _(" with email matching '%s'") % data['email']
        if data['name']:
            # If the value is two words, then assume they are first name and last name
            parts = data['name'].split()
            if len(parts) == 2:
                queryset = queryset.filter(Q(first_name__istartswith=parts[0]) |
                                           Q(last_name__istartswith=parts[1])).distinct()
            else:
                queryset = queryset.filter(Q(first_name__istartswith=data['name']) |
                                           Q(last_name__istartswith=data['name'])).distinct()
            self.desc_ctx['name_filter'] = _(" with name matching '%s'") % data['name']

        return queryset

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['queryset_description'] = self.desc_template % self.desc_ctx
        return context

    def make_inactive(self, request, users):
        return self._change_users_active_status(users, False)

    def make_active(self, request, users):
        return self._change_users_active_status(users, True)

    def _change_users_active_status(self, users, value):
        for user in users:
            if not user.is_superuser:
                user.is_active = value
                user.save()
        messages.info(self.request, _("Users' status successfully changed"))
        return HttpResponseRedirect(reverse(self.current_view))


class UserDetailView(DetailView):
    template_name = 'dashboard/users/detail.html'
    model = User
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        return context


class ProductAlertListView(ListView):
    model = ProductAlert
    form_class = ProductAlertSearchForm
    context_object_name = 'alerts'
    template_name = 'dashboard/users/alerts/list.html'
    paginate_by = 20
    base_description = _('All Alerts')
    description = ''

    def get_queryset(self):
        queryset = self.model.objects.all()
        self.description = self.base_description

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['status']:
            queryset = queryset.filter(status=data['status']).distinct()
            self.description += _(" with status matching '%s'") % data['status']

        if data['name']:
            # If the value is two words, then assume they are first name and
            # last name
            parts = data['name'].split()
            if len(parts) >= 2:
                queryset = queryset.filter(
                    user__first_name__istartswith=parts[0],
                    user__last_name__istartswith=parts[1]
                ).distinct()
            else:
                queryset = queryset.filter(
                    Q(user__first_name__istartswith=parts[0]) |
                    Q(user__last_name__istartswith=parts[-1])
                ).distinct()
            self.description += _(" with customer name matching '%s'") % data['name']

        if data['email']:
            queryset = queryset.filter(
                Q(user__email__icontains=data['email']) |
                Q(email__icontains=data['email'])
            )
            self.description += _(" with customer email matching '%s'") % data['email']

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductAlertListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['queryset_description'] = self.description
        return context


class ProductAlertUpdateView(UpdateView):
    template_name = 'dashboard/users/alerts/update.html'
    model = ProductAlert
    form_class = ProductAlertUpdateForm
    context_object_name = 'alert'

    def get_success_url(self):
        messages.success(self.request, _("Product alert saved"))
        return reverse('dashboard:user-alert-list')


class ProductAlertDeleteView(DeleteView):
    model = ProductAlert
    template_name = 'dashboard/users/alerts/delete.html'
    context_object_name = 'alert'

    def get_success_url(self):
        messages.warning(self.request, _("Product alert deleted"))
        return reverse('dashboard:user-alert-list')
