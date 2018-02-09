from django.core.paginator import EmptyPage, InvalidPage
from django.http import Http404

from . import facet


class BaseSearchHandler(object):

    form = None
    form_class = None
    query = None

    def __init__(self, request_data, full_path, *args, **kwargs):
        self.full_path = full_path
        self.request_data = request_data
        self.form = self.build_form()

    def build_form(self, **kwargs):
        kwargs['selected_facets'] = self.request_data.getlist('selected_facets')
        return self.form_class(self.request_data, **kwargs)

    def get_filters(self, form_data):
        return {}

    def get_search_kwargs(self, search_form, page_no=1):
        form_data = search_form.cleaned_data
        start_offset = (page_no - 1) * form_data['items_per_page']

        return {
            'query': form_data.get('q'),
            'selected_facets': search_form.selected_multi_facets,
            'filters': self.get_filters(form_data),
            'start_offset': start_offset,
            'results_per_page': form_data['items_per_page'],
            'sort_by': search_form.get_sort_params(form_data)
        }

    def get_results(self, request_data):
        """
        Fetches the results via the form.
        """
        try:
            page_no = int(request_data.get('page', 1))
        except (TypeError, ValueError):
            raise Http404("Not a valid number for page.")

        if page_no < 1:
            raise Http404("Pages should be 1 or greater.")

        if not self.form.is_valid():
            raise Http404("Invalid form data.")

        q = self.query(**self.get_search_kwargs(self.form, page_no))
        return q.execute()

    def prepare_context(self, results):
        context = {
            'query': self.form.cleaned_data.get('q'),
            'form': self.form,
            'selected_facets': self.request_data.getlist('selected_facets')
        }

        if results is not None:
            context['paginator'] = results['paginator']
            try:
                context['page_obj'] = results['paginator'].page(
                                                self.request_data.get('page', 1))
            except EmptyPage:
                raise InvalidPage('Invalid page number')

            context['suggestion'] = results['suggestion']

            # Aggregations
            if results['facets']:
                context['facet_data'] = facet.build_oscar_facets(
                    aggs=results['facets'],
                    request_url=self.full_path,
                    selected_facets=self.form.selected_multi_facets
                )
                # Set has_facets to True if at least one facet is non-empty
                context['has_facets'] = any(len(data['results']) > 0 \
                                    for data in context['facet_data'].values())

        return context
