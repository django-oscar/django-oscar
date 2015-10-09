from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.views.generic import ListView

from oscar.apps.dashboard.pages import forms
from oscar.core.loading import get_model
from oscar.core.utils import slugify
from oscar.core.validators import URLDoesNotExistValidator

FlatPage = get_model('flatpages', 'FlatPage')
Site = get_model('sites', 'Site')


class PageListView(ListView):
    """
    View for listing all existing flatpages.
    """
    template_name = 'dashboard/pages/index.html'
    model = FlatPage
    form_class = forms.PageSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    desc_template = u'%(main_filter)s %(title_filter)s'

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
        context = super(PageListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['queryset_description'] = self.desc_template % self.desc_ctx
        return context


class PageCreateView(generic.CreateView):
    template_name = 'dashboard/pages/update.html'
    model = FlatPage
    form_class = forms.PageUpdateForm
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        ctx = super(PageCreateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Create New Page')
        return ctx

    def form_valid(self, form):
        """
        Store new flatpage from form data. Checks wether a site
        is specified for the flatpage or sets the current site by
        default. Additionally, if URL is left blank, a slugified
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
            # use current site as default for new page
            page.save()
            page.sites.add(Site.objects.get_current())

            return HttpResponseRedirect(self.get_success_url(page))

        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)

    def get_success_url(self, page):
        msg = render_to_string('oscar/dashboard/pages/messages/saved.html',
                               {'page': page})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:page-list')


class PageUpdateView(generic.UpdateView):
    """
    View for updating flatpages from the dashboard.
    """
    template_name = 'dashboard/pages/update.html'
    model = FlatPage
    form_class = forms.PageUpdateForm
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        ctx = super(PageUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = self.object.title
        return ctx

    def form_valid(self, form):
        # Ensure saved page is added to the current site
        page = form.save(commit=False)
        if not page.sites.exists():
            page.sites.add(Site.objects.get_current())
        page.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        msg = render_to_string('oscar/dashboard/pages/messages/saved.html',
                               {'page': self.object})
        messages.success(self.request, msg, extra_tags='safe noicon')
        return reverse('dashboard:page-list')


class PageDeleteView(generic.DeleteView):
    template_name = 'dashboard/pages/delete.html'
    model = FlatPage

    def get_success_url(self):
        messages.success(
            self.request, _("Deleted page '%s'") % self.object.title)
        return reverse('dashboard:page-list')
