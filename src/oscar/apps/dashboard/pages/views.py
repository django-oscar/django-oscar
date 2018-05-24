from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic import ListView

from oscar.core.loading import get_classes, get_model
from oscar.core.utils import slugify
from oscar.core.validators import URLDoesNotExistValidator

FlatPage = get_model('flatpages', 'FlatPage')
Site = get_model('sites', 'Site')
PageSearchForm, PageUpdateForm = get_classes('dashboard.pages.forms', ('PageSearchForm', 'PageUpdateForm'))


class PageListView(ListView):
    """
    View for listing all existing flatpages.
    """
    template_name = 'dashboard/pages/index.html'
    model = FlatPage
    form_class = PageSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    desc_template = '%(main_filter)s %(title_filter)s'

    def get_queryset(self):
        """
        Get queryset of all flatpages to be displayed. If a
        search term is specified in the search form, it will be used
        to filter the queryset.
        """
        self.desc_ctx = {
            'main_filter': _('All pages'),
            'title_filter': '',
        }
        queryset = self.model.objects.all().order_by('title')

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['title']:
            queryset = queryset.filter(title__icontains=data['title'])
            self.desc_ctx['title_filter'] \
                = _(" with title containing '%s'") % data['title']

        return queryset

    def get_context_data(self, **kwargs):
        """
        Get context data with *form* and *queryset_description* data
        added to it.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['queryset_description'] = self.desc_template % self.desc_ctx
        return context


class PageCreateUpdateMixin(object):

    template_name = 'dashboard/pages/update.html'
    model = FlatPage
    form_class = PageUpdateForm
    context_object_name = 'page'

    def get_success_url(self):
        msg = render_to_string('oscar/dashboard/pages/messages/saved.html',
                               {'page': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:page-list')

    def form_valid(self, form):
        # Ensure saved page is added to the current site
        page = form.save()
        if not page.sites.exists():
            page.sites.add(Site.objects.get_current())
        self.object = page
        return HttpResponseRedirect(self.get_success_url())


class PageCreateView(PageCreateUpdateMixin, generic.CreateView):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _('Create New Page')
        return ctx

    def form_valid(self, form):
        """
        Store new flatpage from form data.
        Additionally, if URL is left blank, a slugified
        version of the title will be used as URL after checking
        if it is valid.
        """
        # if no URL is specified, generate from title
        page = form.save(commit=False)

        if not page.url:
            page.url = '/%s/' % slugify(page.title)

        try:
            URLDoesNotExistValidator()(page.url)
        except ValidationError:
            pass
        else:
            return super().form_valid(form)

        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)


class PageUpdateView(PageCreateUpdateMixin, generic.UpdateView):
    """
    View for updating flatpages from the dashboard.
    """
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.object.title
        return ctx


class PageDeleteView(generic.DeleteView):
    template_name = 'dashboard/pages/delete.html'
    model = FlatPage

    def get_success_url(self):
        messages.success(
            self.request, _("Deleted page '%s'") % self.object.title)
        return reverse('dashboard:page-list')
