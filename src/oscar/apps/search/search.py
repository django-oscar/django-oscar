import math
import six

from django.conf import settings

from elasticsearch_dsl.faceted_search import (FacetedSearch, DateHistogramFacet, HistogramFacet, RangeFacet,
                                              TermsFacet, FacetedResponse)
from elasticsearch_dsl import Q

from . import utils
from .faceted_search import AutoRangeFacet


FACET_TYPE_MAP = {
    'date_histogram': DateHistogramFacet,
    'histogram': HistogramFacet,
    'range': RangeFacet,
    'terms': TermsFacet,
    'auto_range': AutoRangeFacet
}


class BaseSearch(FacetedSearch):

    index = settings.OSCAR_SEARCH['INDEX_NAME']
    source_fields = []
    settings_key = ''

    def __init__(self, search_filters=None, page_number=1, max_results=0, selected_facets=None, *args, **kwargs):
        self.doc_types = [self.document]
        self.fields = settings.OSCAR_SEARCH[self.settings_key].get('query', {}).get('fields', [])
        self.auto_ranges = {}

        self.aggregate_search = settings.OSCAR_SEARCH[self.settings_key].get('aggregate_search', False)
        if self.aggregate_search:
            self.main_facets = self.get_main_facets()
            self.extra_facets = self.get_extra_facets()

            self.facets = {}
            self.facets.update(self.main_facets)
            self.facets.update(self.extra_facets)

        self._facet_filters = {}
        self.selected_facets_filters = []
        if selected_facets:
            self.selected_facets_filters = self.add_selected_facets_filters(selected_facets)

        self._search_filters = search_filters or {}

        self.page_number = page_number
        self.max_results = max_results

        super(BaseSearch, self).__init__(*args, **kwargs)

    def get_main_facets(self):
        facets = {}
        facet_data = settings.OSCAR_SEARCH[self.settings_key].get('facets', {})
        for name, data in facet_data.items():
            facet_type = data['type']
            facet_class = FACET_TYPE_MAP[facet_type]
            params = data['params']

            if facet_type == 'auto_range':
                params['size'] = 1000000
                self.auto_ranges[name] = data

            facets[name] = facet_class(**params)
        return facets

    def get_extra_facets(self):
        return {}

    def search(self):
        s = self.document.search(index=self.index, using=self.using)
        return s.response_class(FacetedResponse)

    @property
    def doc_type(self):
        return self.document._doc_type.name

    def query(self, search, query):
        if query:
            query_dict = settings.OSCAR_SEARCH[self.settings_key]['query'].copy()
            query_dict['query'] = query
            return search.query(
                query_dict.pop('query_type'),
                **query_dict
            )

        return search

    def aggregate(self, search):
        if self.aggregate_search:
            super(BaseSearch, self).aggregate(search)

    def search_filters(self, search):
        """
                Apply filters to the query. Expects a dict of field: value
                term filters in self.filters
                """
        for field, f in six.iteritems(self._search_filters):
            search = search.filter(Q(f['type'], **f['params']))
        return search

    def add_selected_facets_filters(self, selected_facets):
        filters = []
        for field, value in six.iteritems(selected_facets):
            if field in self.facets:
                agg = self.facets[field]
                field_filter = utils.agg_to_filter(agg, value)
                self._facet_filters[field] = field_filter
                filters.append(field_filter)

        return filters

    def filter_selected_facets(self, search):
        post_filter = Q('match_all')
        for field_filter in self.selected_facets_filters:
            post_filter &= field_filter
        return search.post_filter(post_filter)

    def limit_source(self, search):
        if self.source_fields:
            search = search.source(self.source_fields)

        return search

    def limit_count(self, search):
        if self.max_results:
            start_offset = (self.page_number - 1) * self.max_results
            end_offset = self.page_number * self.max_results
            search = search[start_offset: end_offset]

        return search

    def build_search(self):
        self._filters = self._facet_filters
        search = super(BaseSearch, self).build_search()
        search = self.search_filters(search)
        search = self.filter_selected_facets(search)
        search = self.limit_source(search)
        search = self.limit_count(search)
        return search

    def obj_list_from_results(self, results):
        # Get list of object IDs
        object_pks = [int(item.meta.id) for item in results]
        # Load the corresponding objects
        Model = self.document._doc_type.model
        loaded_objects = Model.objects.in_bulk(object_pks)
        # Create a list in the original result order
        # Skip missing objects - this can happen if ES has gone out of sync with the DB
        return [loaded_objects[pk] for pk in object_pks if pk in loaded_objects]

    def get_auto_range_group_size(self, facet_name, values):
        group_count = self.auto_ranges[facet_name]['group_count']
        return int(math.ceil(len(values) / group_count))

    def auto_range_to_range_facet(self, facet_name, auto_range_facet):
        values = utils.terms_buckets_to_values_list(auto_range_facet['buckets'])

        if not values:
            return {}

        group_size = self.get_auto_range_group_size(facet_name, values)
        chunks = utils.chunks(sorted(values), group_size)

        return {
            facet_name: {
                'buckets': utils.get_auto_ranges(chunks)
            }
        }

    def extract_facets(self, results, facet_names):
        aggregations = getattr(results, 'aggregations', {})

        facets = {}

        for name in facet_names:
            agg = aggregations['_filter_' + name].to_dict()

            if name in self.auto_ranges:
                facets.update(self.auto_range_to_range_facet(name, agg[name]))
            else:
                facets.update(agg)

        return facets

    def extract_suggestion(self, results):
        suggestion = None
        if hasattr(results, 'suggest'):
            sugs = results.suggest['suggestions'][0]['options']
            if len(sugs):
                # Get the string of the top suggest result
                suggestion = sugs[0]['text']

        return suggestion

    def paginate_objects(self, objects, total):
        obj_list = utils.PaginatedObjectList(objects, total)
        return utils.ESPaginator(obj_list, self.max_results)

    def parse_results(self, results):
        ordered_objects = self.obj_list_from_results(results)
        paginator = self.paginate_objects(ordered_objects, results.hits.total)

        suggestion = self.extract_suggestion(results)

        parsed_results = {
            'total': results.hits.total,
            'objects': ordered_objects,
            'paginator': paginator,
            'suggestion': suggestion
        }

        if self.aggregate_search:
            parsed_results['facets'] = self.extract_facets(results, self.main_facets.keys())
            parsed_results['other_aggs'] = self.extract_facets(results, self.extra_facets.keys())

        return parsed_results

    def get_search_results(self):
        results = self.execute()
        return self.parse_results(results)


class BaseAutoSuggestSearch(BaseSearch):

    # make query compulsory argument
    def __init__(self, query, *args, **kwargs):
        kwargs['query'] = query
        kwargs['max_results'] = kwargs.get('max_results') or 5
        super(BaseAutoSuggestSearch, self).__init__(*args, **kwargs)

    # highlight not needed here
    def highlight(self, search):
        return search

    def parse_suggestions(self, results):
        items = []
        for result in results:
            item = {}
            for field in self.source_fields:
                item[field] = getattr(result, field)

            items.append(item)

        return {
            'count': results.hits.total,
            'results': items
        }

    def get_suggestions(self):
        results = self.execute()
        return self.parse_suggestions(results)
