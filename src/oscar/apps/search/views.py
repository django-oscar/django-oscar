from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views import View
from purl import URL

from django.core.paginator import InvalidPage
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView


class BaseSearchView(TemplateView):
    search_handler_class = None
    search_signal = None

    def get_search_handler(self):
        return self.search_handler_class(self.request.GET, self.request.get_full_path())

    def get(self, request, *args, **kwargs):
        try:
            search_handler = self.get_search_handler()
            self.context = search_handler.context
        except InvalidPage:
            messages.error(request, _('The given page number was invalid.'))
            return HttpResponseRedirect(
                self.remove_page_arg(request.get_full_path()))

        # Raise a signal for other apps to hook into for analytics
        self.search_signal.send(
            sender=self, session=request.session,
            user=request.user,
            query=search_handler.form.cleaned_data.get('q'))

        return super(BaseSearchView, self).get(request, *args, **kwargs)

    @staticmethod
    def remove_page_arg(url):
        url = URL(url)
        return url.remove_query_param('page').as_string()

    def get_context_data(self, **kwargs):
        return self.context


class BaseAutoSuggestView(View):

    form_class = None
    query_class = None

    def get_query(self, form):
        return self.query_class(**self.get_query_kwargs(form))

    def get_query_kwargs(self, form):
        kwargs = {
            'query': form.cleaned_data['q']
        }
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.form_class(self.request.GET)
        if form.is_valid():
            s = self.get_query(form)
            results = s.get_suggestions()
            return JsonResponse(results, safe=False)
        else:
            return JsonResponse([], safe=False, status=400)
