from django.core.paginator import EmptyPage, InvalidPage
from django.http import Http404

from oscar.core.loading import get_class

FacetsBuilder = get_class('es_search.facet', 'FacetsBuilder')


class BaseSearchHandler(object):

    form = None
    form_class = None
    query = None

    def __init__(self, request_data, full_path, *args, **kwargs):
        self.full_path = full_path
        self.request_data = request_data
        self.form = self.build_form()

        # Triggers the search. All exceptions (404, Invalid Page) must be raised
        # at init time from inside one of these methods.
        self.results = self.get_results(request_data)
        self.context = self.prepare_context(self.results)

    def get_search_context_data(self, context_object_name=None):
        if context_object_name:
            self.context[context_object_name] = self.context['page_obj'].object_list
        return self.context

    def build_form(self, **kwargs):
        kwargs['selected_facets'] = self.request_data.getlist('selected_facets')
        return self.form_class(self.request_data, **kwargs)

    def get_filters(self, form_data):
        return {}

    def get_search_kwargs(self, search_form, page_number=1):
        form_data = search_form.cleaned_data

        items_per_page = form_data['items_per_page']

        return {
            'query': form_data.get('q'),
            'page_number': page_number,
            'max_results': items_per_page,
            'selected_facets': search_form.selected_multi_facets,
            'search_filters': self.get_filters(form_data),
            'sort': search_form.get_sort_params(form_data)
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

        # check page num doesn't lead to a result window bigger than allowed.
        max_result_window = self.query.document.index_config.get('max_result_window', 10000)
        if (page_no * self.query.items_per_page) > max_result_window:
            raise InvalidPage

        if not self.form.is_valid():
            raise Http404("Invalid form data.")

        q = self.query(**self.get_search_kwargs(self.form, page_no))
        return q.get_search_results()

    def prepare_context(self, results):
        context = {
            'query': self.form.cleaned_data.get('q'),
            'form': self.form,
            'selected_facets': self.request_data.getlist('selected_facets')
        }

        if results is not None:
            context['paginator'] = results['paginator']
            try:
                context['page_obj'] = results['paginator'].page(self.request_data.get('page', 1))
            except EmptyPage:
                raise InvalidPage('Invalid page number')

            context['suggestion'] = results['suggestion']

            # Aggregations
            if results.get('facets'):
                facets_builder = FacetsBuilder(
                    aggs=results['facets'],
                    request_url=self.full_path,
                    selected_facets=self.form.selected_multi_facets,
                    search_class=self.query
                )

                context['facet_data'] = facets_builder.build_facets()

                # Set has_facets to True if at least one facet is non-empty
                context['has_facets'] = any(len(data['results']) > 0 for data in context['facet_data'].values())

        return context
