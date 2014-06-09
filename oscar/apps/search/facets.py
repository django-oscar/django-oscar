from django.conf import settings
from purl import URL


class FacetMunger(object):

    def __init__(self, path, form, results):
        self.base_url = URL(path)
        self.facet_counts = results.facet_counts()
        self.selected_facets = form.selected_multi_facets
        self.results = results

    def facet_data(self):
        if not self.results:
            return {}

        facet_data = {}
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
                'show_count': not is_faceted_already,
                'disabled': count == 0 and not is_faceted_already}
            if field_value in self.selected_facets.get(field_name, []):
                # This filter is selected - build the 'deselect' URL
                datum['selected'] = True
                url = self.base_url.remove_query_param(
                    'selected_facets', '%s:%s' % (
                        field_name, field_value))
                # Don't carry through pagination params
                if url.has_query_param('page'):
                    url = url.remove_query_param('page')
                datum['deselect_url'] = url.as_string()
            else:
                # This filter is not selected - built the 'select' URL
                datum['selected'] = False
                url = self.base_url.append_query_param(
                    'selected_facets', '%s:%s' % (
                        field_name, field_value))
                # Don't carry through pagination params
                if url.has_query_param('page'):
                    url = url.remove_query_param('page')
                datum['select_url'] = url.as_string()

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

            match = '%s_exact:%s' % (facet['field'], query)
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
                }
                if query in self.selected_facets.get(field_name, []):
                    # Selected
                    datum['selected'] = True
                    url = self.base_url.remove_query_param(
                        'selected_facets', match)
                    datum['deselect_url'] = url.as_string()
                    datum['show_count'] = True
                else:
                    datum['selected'] = False
                    url = self.base_url.append_query_param(
                        'selected_facets', match)
                    datum['select_url'] = url.as_string()
            clean_data[key]['results'].append(datum)
