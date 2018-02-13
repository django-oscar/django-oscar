import math
import six

from django.conf import settings

import elasticsearch_dsl as dsl
from oscar.core.loading import get_class, get_classes, get_model

from oscar.apps.search.query import agg_to_filter
from oscar.apps.search import utils

Product = get_model('catalogue', 'Product')
ProductDocument = get_class('catalogue.documents', 'ProductDocument')
BaseSearch, BaseAutoSuggestSearch = get_classes('search.query', ['BaseSearch', 'AutoSuggestSearch'])


class BaseProductSearch(BaseSearch):

    doc_type = 'product'
    document = ProductDocument

    def __init__(self, *args, **kwargs):
        # Currency is required
        self.currency = kwargs.pop('currency')

    def filter_in_stock(self, s):
        query = dsl.Q('match', stock__currency=self.currency) & dsl.Q('range', stock__num_in_stock={'gt': 0})
        return s.filter('nested', path='stock', query=query)


class ProductSearch(BaseProductSearch):

    def __init__(self, query=None, selected_facets=None, filters=None,
                 start_offset=0, results_per_page=None, sort_by=None, **kwargs):
        super(ProductSearch, self).__init__(**kwargs)
        self.query = query
        self.selected_facets = selected_facets if selected_facets else {}
        self.facet_aggs = self.get_facets()
        self.aggs = self.get_aggs()
        self.filters = filters if filters else {}
        self.post_filters = {}
        self.start_offset = start_offset
        self.results_per_page = results_per_page if results_per_page \
            else settings.OSCAR_PRODUCTS_PER_PAGE
        self.sort_by = sort_by
        self.price_ranges = None

    def get_facets(self):
        facets = {}
        for name, data in settings.OSCAR_SEARCH.get('FACETS', {}).items():
            facets[name] = dsl.A(data['type'], **data['params'])
        return facets

    def get_aggs(self):
        return {
            'category': dsl.A('terms', field='categories', size=100000),
        }

    def filter(self, search):
        """
        Apply filters to the query. Expects a dict of field: value
        term filters in self.filters
        """
        for field, f in six.iteritems(self.filters):
            search = search.filter(dsl.Q(f['type'], **f['params']))

        # Filter for the selected currency
        search = search.filter('nested', path='stock',
                               query=dsl.Q('match', stock__currency=self.currency))

        return search

    def post_filter(self, search):
        """
        Apply post filters to the query.
        """
        # Post filter is used for multi-select facets
        post_filter = dsl.Q('match_all')
        for field, value in six.iteritems(self.selected_facets):
            if field in self.facet_aggs:
                agg = self.facet_aggs[field]
                field_filter = agg_to_filter(agg, value)
                self.post_filters[field] = field_filter
                post_filter &= field_filter

        return search.post_filter(post_filter)

    def aggregate(self, search, sniff=False):
        aggregations = self.aggs.copy()
        # If we're just sniffing for price range, we don't need facets
        if not sniff:
            aggregations.update(self.facet_aggs)

        for name, agg in six.iteritems(aggregations):
            agg_filter = dsl.Q('match_all')
            for field, filter in six.iteritems(self.post_filters):
                if not field == name:
                    agg_filter &= filter
            search.aggs.bucket(
                '_filter_' + name,
                'filter',
                filter=agg_filter
            ).bucket(name, agg)

    def get_price_ranges(self, sniff_response):
        prices = []
        for p in sniff_response:
            if 'stock' in p:
                # Take the first stock record we find that has the right currency
                # TODO is there any way to filter these in ES?
                stocks = [x for x in p['stock'] if x['currency'] == self.currency]
                if stocks:
                    prices.append(stocks[0]['price'])

        price_count = len(prices)
        if price_count < 10:
            return

        n_groups = getattr(settings, 'OSCAR_PRICE_FACET_COUNT', 5)
        group_size = int(math.ceil(price_count / n_groups))
        chunks = utils.chunks(prices, group_size)
        ranges = []
        last_breakpoint = 0
        for chunk in chunks:
            range_start = float(chunk[0])
            range_end = float(chunk[-1])
            magnitude = pow(10, int(math.log10(range_end)))
            spread = int(range_end - range_start)
            # If everything in this chunk is a similar price, then we need
            # to use a smaller interval
            while spread < magnitude and magnitude > 10:
                magnitude = magnitude / 10

            rounded_range_end = int(math.ceil(range_end / magnitude) * magnitude)

            # It is possible that items in this chunk fall in the previous range
            count = len(chunk)
            for item in chunk:
                if item < last_breakpoint:
                    ranges[-1]['count'] += 1
                    count -= 1

            if rounded_range_end > last_breakpoint:
                ranges.append({
                    'start': last_breakpoint,
                    'end': rounded_range_end,
                    'count': count
                })
                last_breakpoint = rounded_range_end

        return ranges

    def get_basic_search(self):
        s = self.search_instance()
        if self.query:
            s = self.add_multi_match(s, self.query)
        s = self.filter(s)
        s = self.post_filter(s)
        return s

    def sniff_price_range(self):
        s = self.get_basic_search()
        self.aggregate(s, sniff=True)
        # Fetch only prices
        s = s.params(_source=['stock'])
        s = s.sort({
            'stock.price': {
                'order': 'asc',
                'mode': 'min',
                'nested_path': 'stock',
                'nested_filter': {
                    'match': {'stock.currency': self.currency}
                }
            }
        })
        s = s[0:10000]

        response = s.execute()
        # We have anough to work out nice price ranges now
        self.price_ranges = self.get_price_ranges(response)

    def build_search(self):
        s = self.get_basic_search()
        if self.query:
            s = s.suggest('suggestions', self.query,
                          phrase={'field': 'raw_title', 'size': 1, 'max_errors': 2.0})
        self.aggregate(s)
        # Pagination
        s = s[self.start_offset:self.start_offset + self.results_per_page]
        # Sorting
        if self.sort_by:
            s = s.sort(self.sort_by)
        return s

    def parse_response(self, response):
        ordered_objects = self.obj_list_from_results(response)
        obj_list = utils.PaginatedObjectList(ordered_objects, response.hits.total)
        paginator = utils.ESPaginator(obj_list, self.results_per_page)

        # Go down one level into the aggregations, removing the outer _filter_
        result_aggs = getattr(response, 'aggregations', {})
        facets = {}

        for name in self.facet_aggs:
            facets.update(result_aggs['_filter_' + name].to_dict())

        other_aggs = {}
        for name in self.aggs:
            other_aggs.update(result_aggs['_filter_' + name].to_dict())

        suggestion = None
        if hasattr(response, 'suggest'):
            sugs = response.suggest['suggestions'][0]['options']
            if len(sugs):
                # Get the string of the top suggest result
                suggestion = sugs[0]['text']

        results = {
            'total': response.hits.total,
            'objects': ordered_objects,
            'facets': facets,
            'other_aggs': other_aggs,
            'paginator': paginator,
            'suggestion': suggestion,
            'price_ranges': self.price_ranges
        }

        return results

    def execute(self):
        """
        Executes a search and parses the response.
        """
        if 'price' not in self.filters and settings.OSCAR_SEARCH['SHOW_PRICE_RANGE_FACET']:
            self.sniff_price_range()
        s = self.build_search()
        return self.parse_response(s.execute())


class RelatedProductSearch(BaseProductSearch):

    def __init__(self, product_ids, **kwargs):
        super(RelatedProductSearch, self).__init__(**kwargs)
        self.products = Product.browsable.filter(pk__in=product_ids)
        self.product_docs = [{
            '_index': self.index,
            '_type': self.doc_type,
            '_id': p.pk
        } for p in self.products]

    def get_related_products(self, num=5, category_id=None):
        compare_fields = getattr(settings, 'OSCAR_RELATED_PRODUCT_FIELDS', ['title', 'description'])

        if not hasattr(self, '_results'):
            s = self.search_instance()
            s = s.query(
                'more_like_this',
                fields=compare_fields,
                docs=self.product_docs
            )

            s = self.filter_in_stock(s)

            if category_id:
                s = s.filter(dsl.Q('term', categories=category_id))

            s = s[0:num]
            self._results = s.execute()
        return self.obj_list_from_results(self._results)


class CatalogueAutoSuggestSearch(BaseProductSearch, BaseAutoSuggestSearch):

    returned_fields = ['title', 'url']

    def get_search_filters(self, search, search_form):
        category_id = search_form.cleaned_data.get('category')
        if category_id:
            search = search.filter(dsl.Q('term', categories=category_id))
        return search


class TopProductsSearch(BaseProductSearch):

    def get_top_products(self, category_id=None, num=10):
        # We have to use the low level client, not DSL
        s = self.search_instance()

        if category_id:
            s = s.filter(dsl.Q('term', categories=category_id))

        s = self.filter_in_stock(s)

        s = s.sort('-score')
        s = s[0:num]

        results = s.execute()

        return self.obj_list_from_results(results)
