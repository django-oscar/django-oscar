from django.db.models.loading import get_model
from django.template.defaultfilters import slugify
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.views import generic
from django.views.generic import ListView
from django.contrib import messages

from oscar.core.validators import URLDoesNotExistValidator
from oscar.apps.dashboard.pages import forms

FlatPage = get_model('flatpages', 'FlatPage')
Site = get_model('sites', 'Site')


class PageListView(ListView):
    """
    View for listing all existing flatpages.
    """
    template_name = 'dashboard/pages/index.html'
    current_view = 'dashboard:pages-index'
    model = FlatPage
    form_class = forms.PageSearchForm
    paginate_by = 25
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
            self.desc_ctx['title_filter'] = _(" with title containing '%s'") % data['title']

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
    """
    View for creating a flatpage from dashboard.
    """
    template_name = 'dashboard/pages/update.html'
    model = FlatPage
    form_class = forms.PageUpdateForm
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        """
        Get context data with additional *title* object.
        """
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

            # use current site as default for new page
            page.save()
            page.sites.add(Site.objects.get_current())

            return HttpResponseRedirect(self.get_success_url(page))

        except ValidationError:
            pass

        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)

    def get_success_url(self, page):
        messages.success(self.request, _("Created new page '%s'") % page.title)
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
        """
        Get context data with additional *title* and *page* objects attached.
        """
        ctx = super(PageUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Update Page')
        return ctx

    def form_valid(self, form):
        """
        Store updated flatpage from form data. Checks wether a site
        is specified for the flatpage or sets the current site by
        default.
        """
        page = form.save(commit=False)

        if not page.sites.count():
            page.sites.add(Site.objects.get_current())
        page.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """
        Get URL to redirect to when updating page was successful.
        """
        messages.success(self.request, _("Updated page '%s'") % self.object.title)
        return reverse('dashboard:page-list')


class PageDeleteView(generic.DeleteView):
    """
    View for deleting flatpages from the dashboard. It performs an
    'are you sure?' check before actually deleting the page.
    """
    template_name = 'dashboard/pages/delete.html'
    model = FlatPage

    def get_success_url(self):
        """
        Get URL to redirect to when deleting page is succesful.
        """
        messages.success(self.request, _("Deleted page '%s'") % self.object.title)
        return reverse('dashboard:page-list')
