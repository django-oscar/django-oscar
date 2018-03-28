import math

from django.core.paginator import Paginator, Page

import elasticsearch_dsl as dsl

from .faceted_search import AutoRangeFacet


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def terms_buckets_to_values_list(buckets):
    values = []
    for bucket in buckets:
        values.extend([bucket['key']] * bucket['doc_count'])

    return values


def get_auto_ranges(chunks):
    """
    Generate a set of ranges given an iterable of chunks of values.
    Works only for integer values.
    """

    ranges = []
    last_breakpoint = 0
    for chunk in chunks:
        range_start = float(chunk[0])
        range_end = float(chunk[-1])
        spread = int(range_end - range_start)
        if spread > 0:
            # Determine the order of magnitude of the range_end
            magnitude = pow(10, int(math.log10(range_end)))
        else:
            magnitude = 1

        # If everything in this chunk is a similar value, then we need
        # to use a smaller interval
        while spread < magnitude and magnitude > 10:
            magnitude = magnitude / 10

        rounded_range_end = int(math.ceil(range_end / magnitude) * magnitude)

        # It is possible that items in this chunk fall in the previous range
        count = len(chunk)
        for item in chunk:
            if item < last_breakpoint:
                ranges[-1]['doc_count'] += 1
                count -= 1

        if rounded_range_end >= last_breakpoint:
            ranges.append({
                'from': last_breakpoint,
                'to': rounded_range_end,
                'doc_count': count
            })
            last_breakpoint = rounded_range_end + 1

    return ranges


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
            query['lte'] = float(to_value)
        field_filters.append(dsl.Q('range', **{agg._params['field']: query}))
    return field_filters


def agg_terms_to_filters(agg, values):
    return [dsl.Q('term', **{agg._params['field']: value}) for value in values]


def agg_histogram_to_filters(agg, values):
    return [dsl.Q('range', **{agg._params['field']: {'gte': value, 'lt': int(agg._params['interval']) + float(value)}})
            for value in values]


AGG_TO_FILTERS = {
    AutoRangeFacet: agg_range_to_filters,
    dsl.RangeFacet: agg_range_to_filters,
    dsl.TermsFacet: agg_terms_to_filters,
    dsl.HistogramFacet: agg_histogram_to_filters,
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


class PaginatedObjectList(object):

    def __init__(self, object_list, total):
        self.object_list = object_list
        self.total = total

    def count(self):
        return self.total

    def __iter__(self):
        for obj in self.object_list:
            yield obj


class ESPaginator(Paginator):
    """
    Override the core Paginator so that it doesn't need a complete
    list of objects. Use the paginated result set from ES instead.
    """

    def page(self, number):
        # Data has been sliced already, just return the full list
        number = self.validate_number(number)
        return Page(self.object_list, number, self)
