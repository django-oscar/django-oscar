from django.db.models import Q, get_model
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic

from oscar.apps.dashboard.users import forms
from oscar.views.generic import BulkEditMixin

Notification = get_model('notification', 'notification')


class IndexView(generic.ListView, BulkEditMixin):
    template_name = 'dashboard/users/index.html'
    paginate_by = 25
    model = User
    actions = ('make_active', 'make_inactive', )
    current_view = 'dashboard:users-index'
    form_class = forms.UserSearchForm
    base_description = 'All users'
    description = ''

    def get_queryset(self):
        queryset = self.model.objects.all().order_by('-date_joined')
        self.description = self.base_description

        if 'email' not in self.request.GET:
            self.form = self.form_class()
            return queryset

        self.form = self.form_class(self.request.GET)

        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['email']:
            queryset = queryset.filter(email__startswith=data['email'])
            self.description += " with email matching '%s'" % data['email']
        if data['name']:
            # If the value is two words, then assume they are first name and last name
            parts = data['name'].split()
            if len(parts) == 2:
                queryset = queryset.filter(Q(first_name__istartswith=parts[0]) |
                                           Q(last_name__istartswith=parts[1])).distinct()
            else:
                queryset = queryset.filter(Q(first_name__istartswith=data['name']) |
                                           Q(last_name__istartswith=data['name'])).distinct()
            self.description += " with name matching '%s'" % data['name']

        return queryset

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['queryset_description'] = self.description
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
        messages.info(self.request, 'Users\' status successfully changed')
        return HttpResponseRedirect(reverse(self.current_view))


class UserDetailView(generic.DetailView):
    template_name = 'dashboard/users/detail.html'
    model = User
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        return context


class NotificationListView(generic.ListView, BulkEditMixin):
    model = Notification
    form_class = forms.NotificationSearchForm
    context_object_name = 'notification_list'
    template_name = 'dashboard/notification/list.html'
    paginate = 25
    actions = ('update_selected_notification_status',)
    base_description = 'All notifications'
    checkbox_object_name = 'notification'
    description = ''

    def get_queryset(self):
        queryset = self.model.objects.select_subclasses()
        self.description = self.base_description

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['status']:
            queryset = queryset.filter(status=data['status']).distinct()
            self.description += " with status matching '%s'" % data['status']

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
            self.description += " with customer name matching '%s'" % data['name']

        if data['email']:
            queryset = queryset.filter(
                Q(user__email__icontains=data['email']) |
                Q(email__icontains=data['email'])
            )
            self.description += " with customer email matching '%s'" % data['email']

        return queryset

    def update_selected_notification_status(self, request, notifications):
        new_status = request.POST.get('status')
        for notification in notifications:
            notification.status = new_status
            notification.save()
        return HttpResponseRedirect(reverse('dashboard:user-notification-list'))

    def get_context_data(self, **kwargs):
        context = super(NotificationListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['notification_form'] = forms.NotificationUpdateForm
        context['queryset_description'] = self.description
        return context


class NotificationUpdateView(generic.UpdateView):
    template_name = 'dashboard/notification/update.html'
    model = Notification
    form_class = forms.NotificationUpdateForm
    context_object_name = 'notification'

    def get_success_url(self):
        return reverse('dashboard:user-notification-list')


class NotificationDeleteView(generic.DeleteView):
    model = Notification
    template_name = 'dashboard/notification/delete.html'
    context_object_name = 'notification'

    def get_success_url(self):
        return reverse('dashboard:user-notification-list')
