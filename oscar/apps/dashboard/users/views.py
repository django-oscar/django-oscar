from django.views.generic import ListView, DetailView
from django.contrib.auth.models import User

class IndexView(ListView):
    template_name = 'dashboard/users/index.html'
    paginate_by = 25
    model = User


    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context


class UserDetailView(DetailView):
    template_name = 'dashboard/users/detail.html'
    model = User
