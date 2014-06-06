from django.conf import settings
from purl import URL
from six.moves import map


def facet_data(request, form, results):  # noqa (too complex (10))
    """
    Convert Haystack's facet data into a more useful datastructure that
    templates can use without having to manually construct URLs
    """
    if not results:
        return {}

    base_url = URL(request.get_full_path())
    facet_counts = results.facet_counts()
    selected_facets = form.selected_multi_facets

    facet_data = {}
    for key, facet in settings.OSCAR_SEARCH_FACETS['fields'].items():
        facet_data[key] = {
            'name': facet['name'],
            'results': []}
        for field_value, count in facet_counts['fields'][key]:
            field_name = '%s_exact' % facet['field']
            is_faceted_already = field_name in selected_facets
            datum = {
                'name': field_value,
                'count': count,
                'show_count': not is_faceted_already,
                'disabled': count == 0 and not is_faceted_already}
            if field_value in selected_facets.get(field_name, []):
                # This filter is selected - build the 'deselect' URL
                datum['selected'] = True
                url = base_url.remove_query_param(
                    'selected_facets', '%s:%s' % (
                        field_name, field_value))
                # Don't carry through pagination params
                if url.has_query_param('page'):
                    url = url.remove_query_param('page')
                datum['deselect_url'] = url.as_string()
            else:
                # This filter is not selected - built the 'select' URL
                datum['selected'] = False
                url = base_url.append_query_param(
                    'selected_facets', '%s:%s' % (
                        field_name, field_value))
                # Don't carry through pagination params
                if url.has_query_param('page'):
                    url = url.remove_query_param('page')
                datum['select_url'] = url.as_string()
            facet_data[key]['results'].append(datum)

    # Query facets
    for key, facet in settings.OSCAR_SEARCH_FACETS['queries'].items():
        facet_data[key] = {
            'name': facet['name'],
            'results': []}
        for field_value, query in facet['queries']:
            field_name = '%s_exact' % facet['field']
            match = '%s_exact:%s' % (facet['field'], query)
            if match not in facet_counts['queries']:
                datum = {
                    'name': field_value,
                    'count': 0,
                }
            else:
                datum = {
                    'name': field_value,
                    'count': facet_counts['queries'][match],
                }
                if selected_facets.get(field_name, None) == query:
                    # Selected
                    datum['selected'] = True
                    url = base_url.remove_query_param(
                        'selected_facets', match)
                    datum['deselect_url'] = url.as_string()
                else:
                    datum['selected'] = False
                    url = base_url.append_query_param(
                        'selected_facets', match)
                    datum['select_url'] = url.as_string()

            facet_data[key]['results'].append(datum)

    return facet_data
