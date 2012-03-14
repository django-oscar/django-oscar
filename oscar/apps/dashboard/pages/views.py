from django.db.models.loading import get_model
from django.http import HttpResponseRedirect

from django.contrib import messages
from django.views import generic
from django.views.generic import ListView
from django.core.urlresolvers import reverse
from oscar.apps.dashboard.pages import forms 

FlatPage = get_model('flatpages', 'FlatPage')


class PageListView(ListView):
    template_name = 'dashboard/pages/index.html'
    current_view = 'dashboard:pages-index'
    model = FlatPage 
    form_class = forms.PageSearchForm
    paginate_by = 25
    base_description = 'All pages'
    description = ''

    def get_queryset(self):
        self.description = self.base_description
        queryset = self.model.objects.all().order_by('title')

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['title']:
            queryset = queryset.filter(title__contains=data['title'])
            self.description += " with title containing '%s'" % data['title']

        return queryset

    def get_context_data(self, **kwargs):
        context = super(PageListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['queryset_description'] = self.description
        return context


class PageCreateView(generic.CreateView):
    template_name = 'dashboard/pages/update.html'
    model = FlatPage
    form_class = forms.PageUpdateForm
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        ctx = super(PageCreateView, self).get_context_data(**kwargs)
        ctx['title'] = 'Create New Page'
        return ctx

    def form_valid(self, form):
        ##FIXME: validation of URL is required
        if True:
            page = form.save()
            return HttpResponseRedirect(self.get_success_url(page))

        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)

    def get_success_url(self, page):
        messages.success(self.request, "Created new page '%s'" % page.title)
        return reverse('dashboard:page-list')


class PageUpdateView(generic.UpdateView):
    template_name = 'dashboard/pages/update.html'
    model = FlatPage
    form_class = forms.PageUpdateForm

    def get_context_data(self, **kwargs):
        ctx = super(PageUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = 'Update Page'
        return ctx

    def form_valid(self, form):
        ##FIXME: validation of URL is required
        if True:
            page = form.save()
            return HttpResponseRedirect(self.get_success_url())

        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)

    def get_success_url(self, page):
        messages.success(self.request, "Updated page '%s'" % self.object.title)
        return reverse('dashboard:page-list')
