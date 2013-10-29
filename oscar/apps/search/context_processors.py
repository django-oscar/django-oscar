from oscar.core.loading import get_class

MultiFacetedSearchForm = get_class('search.forms', 'MultiFacetedSearchForm')


def search_form(request):
    """
    Ensure that the search form is available site wide
    """
    return {'search_form': MultiFacetedSearchForm(request.GET)}
