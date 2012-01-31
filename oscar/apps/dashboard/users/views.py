from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic import ListView, DetailView

from oscar.apps.dashboard.views import BulkEditMixin


class IndexView(ListView, BulkEditMixin):
    template_name = 'dashboard/users/index.html'
    paginate_by = 25
    model = User
    actions = ('make_active', 'make_inactive', )
    current_view = 'dashboard:users-index'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
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


class UserDetailView(DetailView):
    template_name = 'dashboard/users/detail.html'
    model = User

