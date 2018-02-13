from collections import OrderedDict
from purl import URL
from six import iteritems

from django.conf import settings


class BaseFacet(object):

    facet_name = None

    def __init__(self, name, agg, request_url, selected_facets={}):
        self.field_name = name
        self.agg = agg
        self.selected_facets = selected_facets
        self.base_url = URL(request_url)
        if 'buckets' in agg:
            self.buckets = agg['buckets']
            # If not, the subclass needs to find the right buckets...

    def get_field_value(self, bucket):
        return str(bucket['key'])

    def get_display_name(self, bucket):
        return self.get_field_value(bucket)

    def get_select_url(self, field_value):
        url = self.base_url.append_query_param(
            'selected_facets', '%s:%s' % (self.field_name, field_value))
        return self.strip_pagination(url)

    def get_deselect_url(self, field_value):
        url = self.base_url.remove_query_param(
            'selected_facets', '%s:%s' % (self.field_name, field_value))
        return self.strip_pagination(url)

    @staticmethod
    def strip_pagination(url):
        if url.has_query_param('page'):
            url = url.remove_query_param('page')
        return url.as_string()

    def get_facet(self):
        facets = []
        for bucket in self.buckets:
            field_value = self.get_field_value(bucket)
            facet = {
                'name': self.get_display_name(bucket),
                'count': bucket['doc_count'],
                'show_count': True,
                'selected': False,
                'disabled': (int(bucket['doc_count']) == 0)
            }
            if field_value in self.selected_facets.get(self.field_name, []):
                # This filter is selected - build the 'deselect' URL
                facet['selected'] = True
                facet['deselect_url'] = self.get_deselect_url(field_value)
            else:
                facet['select_url'] = self.get_select_url(field_value)

            facets.append(facet)

        facet_name = self.facet_name if self.facet_name else self.field_name.capitalize()
        # TODO this is rather hacky - is there a better way to get this label?
        user_defined_facets = settings.OSCAR_SEARCH.get('FACETS', {})

        if self.field_name in user_defined_facets:
            facet_name = user_defined_facets[self.field_name]['label']

        return {
            'name': facet_name,
            'results': facets
        }


class BaseRangeFacet(BaseFacet):

    """
    NOTE: Elasticsearch's range aggregations are bit awkward because
    they exclude the "to" value from the range. There is jiggery pokery here
    to alter the display value of the upper bound.

    Currently this code assumes integer ranges only.
    """

    @staticmethod
    def get_field_value(bucket):
        from_value = bucket.get('from', '')
        to_value = bucket.get('to', '')
        return '{}-{}'.format(from_value, to_value)

    @staticmethod
    def get_display_name(bucket):
        from_value = int(bucket.get('from', 0))
        to_value = int(bucket.get('to', 0))
        if not from_value:
            return 'Up to {}'.format(to_value - 1)
        if not to_value:
            return '{} and above'.format(from_value)
        return '{} to {}'.format(from_value, to_value - 1)

    def get_facet(self):
        # Horrible ugly check to return an empty result if all ranges are empty
        total_count = sum([b['doc_count'] for b in self.buckets])
        if total_count == 0:
            return {
                'name': self.facet_name if self.facet_name else self.field_name.capitalize(),
                'results': []
            }

        return super(BaseRangeFacet, self).get_facet()


FACET_CLASSES = {
    'range': BaseRangeFacet
}


def get_facet_class(field):
    try:
        user_defined_facets = settings.OSCAR_SEARCH.get('FACETS', {})
        facet_type = user_defined_facets.get(field, {})['type']
        return FACET_CLASSES[facet_type]
    except KeyError:
        return BaseFacet


def build_oscar_facets(aggs, request_url, selected_facets):
    """
    Converts aggregations from ES into facets that Oscar templates will grok.
    """
    facet_data = {}
    for field, agg in iteritems(aggs):
        if not isinstance(agg, dict):
            continue
        Facet = get_facet_class(field)
        facet_data[field] = Facet(name=field,
                                  agg=agg,
                                  request_url=request_url,
                                  selected_facets=selected_facets).get_facet()

    # Sort facets based on the order supplied in settings
    facet_order = getattr(settings, 'OSCAR_FACET_ORDER', [])
    sorted_facet_data = []
    for field in facet_order:
        if field in facet_data:
            sorted_facet_data.append((field, facet_data.pop(field)))

    # If anything is left, leave it at the end
    for field in list(facet_data):
        sorted_facet_data.append((field, facet_data.pop(field)))

    return OrderedDict(sorted_facet_data)
