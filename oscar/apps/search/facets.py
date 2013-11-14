from django.conf import settings
from purl import URL


def facet_data(request, form, results):
    """
    Convert Haystack's facet data into a more useful datastructure that
    templates can use without having to manually construct URLs
    """
    facet_data = {}
    base_url = URL(request.get_full_path())
    facet_counts = results.facet_counts()

    # Field facets
    selected = dict(
        map(lambda x: x.split(':'), form.selected_facets))
    for field, facets in facet_counts['fields'].items():
        facet_data[field] = []
        for name, count in facets:
            # Ignore zero-count facets for field
            if count == 0:
                continue
            field_filter = '%s_exact' % field
            datum = {
                'name': name,
                'count': count}
            if selected.get(field_filter, None) == name:
                # This filter is selected - build the 'deselect' URL
                datum['selected'] = True
                url = base_url.remove_query_param(
                    'selected_facets', '%s:%s' % (
                        field_filter, name))
                datum['deselect_url'] = url.as_string()
            else:
                # This filter is not selected - built the 'select' URL
                datum['selected'] = False
                url = base_url.append_query_param(
                    'selected_facets', '%s:%s' % (
                        field_filter, name))
                datum['select_url'] = url.as_string()
            facet_data[field].append(datum)

    # Query facets
    for key, facet in settings.OSCAR_SEARCH_FACETS['queries'].items():
        facet_data[key] = []
        for name, query in facet_counts['queries'].items():
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
                facet_data[key].append(datum)

    return facet_data
