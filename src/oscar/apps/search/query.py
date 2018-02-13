from django.conf import settings
import elasticsearch_dsl as dsl
from oscar.core.loading import get_model


Product = get_model('catalogue', 'Product')


def agg_range_to_filters(agg, values):
    """
    Expects a range to be supplied as `from`-`to`
    """
    field_filters = []
    for value in values:
        try:
            from_value, to_value = value.split('-')
        except ValueError:
            # Ignore malformed inputs
            continue
        query = {}
        if from_value:
            query['gte'] = float(from_value)
        if to_value:
            query['lt'] = float(to_value)
        field_filters.append(dsl.Q('range', **{agg.field: query}))
    return field_filters


def agg_terms_to_filters(agg, values):
    return [dsl.Q('term', **{agg.field: value}) for value in values]


def agg_histogram_to_filters(agg, values):
    return [dsl.Q('range', **{agg.field: {'gte': value, 'lt': int(agg.interval) + int(value)}})
            for value in values]


AGG_TO_FILTERS = {
    dsl.aggs.Range: agg_range_to_filters,
    dsl.aggs.Terms: agg_terms_to_filters,
    dsl.aggs.Histogram: agg_histogram_to_filters,
}


def agg_to_filter(agg, value):
    if not isinstance(value, list):
        value = [value]
    try:
        filter_list = AGG_TO_FILTERS[agg.__class__](agg, value)
    except KeyError:
        raise NotImplementedError(
            'Unable to create filter for aggregation of type %s' %
            agg.__class__.__name__)

    if len(filter_list):
        filter = filter_list[0]
        for f in filter_list[1:]:
            filter |= f
    else:
        filter = dsl.Q()
    return filter


class BaseSearch(object):

    index = settings.OSCAR_SEARCH.get('INDEX_NAME', 'oscar')
    document = None

    def search_instance(self):
        return self.document.search(index=self.index)

    @staticmethod
    def obj_list_from_results(results):
        # Get list of object IDs
        product_pks = [int(item.meta.id) for item in results]
        # Load the corresponding products
        loaded_objects = Product.objects.in_bulk(product_pks)
        # Create a list in the original result order
        # Skip missing objects - this can happen if ES has gone out of sync with the DB
        return [loaded_objects[pk] for pk in product_pks if pk in loaded_objects]

    def add_multi_match(self, search, query_string):
        query_dict = settings.OSCAR_SEARCH['SEARCH_CONFIG'][self.document._doc_type.name].copy()
        query_dict['query'] = query_string
        return search.query(
            query_dict.pop('query_type'),
            **query_dict
        )


class AutoSuggestSearch(BaseSearch):

    returned_fields = []

    def get_search_filters(self, search, search_form):
        return search

    def get_suggestions(self, search_form, max=5):
        # We have to use the low level client, not DSL
        s = self.search_instance()

        query = search_form.cleaned_data['q']
        s = self.add_multi_match(s, query)

        s = self.get_search_filters(s.source(self.returned_fields), search_form)

        s = s[0:max]

        results = s.execute()

        items = []
        for result in results:
            item = {}
            for field in self.returned_fields:
                item[field] = getattr(result, field)

            items.append(item)

        return {
            'count': results.hits.total,
            'results': items
        }
