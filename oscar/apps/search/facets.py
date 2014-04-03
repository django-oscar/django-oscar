from django.conf import settings
from purl import URL
from six.moves import map


def facet_data(request, form, results):  # noqa (too complex (10))
    """
    Convert Haystack's facet data into a more useful datastructure that
    templates can use without having to manually construct URLs
    """
    facet_data = {}
    if not results:
        return facet_data

    base_url = URL(request.get_full_path())
    facet_counts = results.facet_counts()

    # Field facets
    valid_facets = [f for f in form.selected_facets if ':' in f]
    selected = dict(
        map(lambda x: x.split(':', 1), valid_facets))
    for key, facet in settings.OSCAR_SEARCH_FACETS['fields'].items():
        facet_data[key] = {
            'name': facet['name'],
            'results': []}
        for name, count in facet_counts['fields'][key]:
            # Ignore zero-count facets for field
            if count == 0:
                continue
            field_filter = '%s_exact' % facet['field']
            datum = {
                'name': name,
                'count': count}
            if selected.get(field_filter, None) == name:
                # This filter is selected - build the 'deselect' URL
                datum['selected'] = True
                url = base_url.remove_query_param(
                    'selected_facets', '%s:%s' % (
                        field_filter, name))
                # Don't carry through pagination params
                if url.has_query_param('page'):
                    url = url.remove_query_param('page')
                datum['deselect_url'] = url.as_string()
            else:
                # This filter is not selected - built the 'select' URL
                datum['selected'] = False
                url = base_url.append_query_param(
                    'selected_facets', '%s:%s' % (
                        field_filter, name))
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
        for name, query in facet['queries']:
            field_filter = '%s_exact' % facet['field']
            match = '%s_exact:%s' % (facet['field'], query)
            if match not in facet_counts['queries']:
                datum = {
                    'name': name,
                    'count': 0,
                }
            else:
                datum = {
                    'name': name,
                    'count': facet_counts['queries'][match],
                }
                if selected.get(field_filter, None) == query:
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
