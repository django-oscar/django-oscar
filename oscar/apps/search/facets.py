from django.conf import settings
from purl import URL
from haystack.query import SearchQuerySet


def base_sqs():
    """
    Return the base SearchQuerySet for Haystack searches.
    """
    sqs = SearchQuerySet()
    for facet in settings.OSCAR_SEARCH_FACETS['fields'].values():
        options = facet.get('options', {})
        sqs = sqs.facet(facet['field'], **options)
    for facet in settings.OSCAR_SEARCH_FACETS['queries'].values():
        for query in facet['queries']:
            sqs = sqs.query_facet(facet['field'], query[1])
    return sqs


class FacetMunger(object):

    def __init__(self, path, selected_multi_facets, facet_counts):
        self.base_url = URL(path)
        self.selected_facets = selected_multi_facets
        self.facet_counts = facet_counts

    def facet_data(self):
        facet_data = {}
        # Haystack can return an empty dict for facet_counts when e.g. Solr
        # isn't running. Skip facet munging in that case.
        if self.facet_counts:
            self.munge_field_facets(facet_data)
            self.munge_query_facets(facet_data)
        return facet_data

    def munge_field_facets(self, clean_data):
        for key, facet in settings.OSCAR_SEARCH_FACETS['fields'].items():
            self.munge_field_facet(key, facet, clean_data)

    def munge_field_facet(self, key, facet, clean_data):
        clean_data[key] = {
            'name': facet['name'],
            'results': []}
        for field_value, count in self.facet_counts['fields'][key]:
            field_name = '%s_exact' % facet['field']
            is_faceted_already = field_name in self.selected_facets
            datum = {
                'name': field_value,
                'count': count,
                # We don't show facet counts if a this field is already being
                # faceted (as we don't know them)
                'show_count': not is_faceted_already,
                'disabled': count == 0 and not is_faceted_already,
                'selected': False
            }
            if field_value in self.selected_facets.get(field_name, []):
                # This filter is selected - build the 'deselect' URL
                datum['selected'] = True
                url = self.base_url.remove_query_param(
                    'selected_facets', '%s:%s' % (
                        field_name, field_value))
                datum['deselect_url'] = self.strip_pagination(url)
            else:
                # This filter is not selected - built the 'select' URL
                url = self.base_url.append_query_param(
                    'selected_facets', '%s:%s' % (
                        field_name, field_value))
                datum['select_url'] = self.strip_pagination(url)

            clean_data[key]['results'].append(datum)

    def munge_query_facets(self, clean_data):
        for key, facet in settings.OSCAR_SEARCH_FACETS['queries'].items():
            self.munge_query_facet(key, facet, clean_data)

    def munge_query_facet(self, key, facet, clean_data):
        clean_data[key] = {
            'name': facet['name'],
            'results': []}
        # Loop over the queries in OSCAR_SEARCH_FACETS rather than the returned
        # facet information from the search backend.
        for field_value, query in facet['queries']:
            field_name = '%s_exact' % facet['field']
            is_faceted_already = field_name in self.selected_facets

            match = '%s:%s' % (field_name, query)
            if match not in self.facet_counts['queries']:
                # This query was not returned
                datum = {
                    'name': field_value,
                    'count': 0,
                    'show_count': True,
                    'disabled': True,
                }
            else:
                count = self.facet_counts['queries'][match]
                datum = {
                    'name': field_value,
                    'count': count,
                    'show_count': not is_faceted_already,
                    'disabled': count == 0 and not is_faceted_already,
                    'selected': False,
                }
                if query in self.selected_facets.get(field_name, []):
                    # Selected
                    datum['selected'] = True
                    datum['show_count'] = True
                    url = self.base_url.remove_query_param(
                        'selected_facets', match)
                    datum['deselect_url'] = self.strip_pagination(url)
                else:
                    url = self.base_url.append_query_param(
                        'selected_facets', match)
                    datum['select_url'] = self.strip_pagination(url)
            clean_data[key]['results'].append(datum)

    def strip_pagination(self, url):
        if url.has_query_param('page'):
            url = url.remove_query_param('page')
        return url.as_string()
