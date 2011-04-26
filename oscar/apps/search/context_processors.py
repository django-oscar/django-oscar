from oscar.core.loading import import_module
search_forms = import_module('search.forms', ['MultiFacetedSearchForm'])

def search_form(request):
    u"""
    Ensures that the search form is available site wide
    """
    return {'search_form': search_forms.MultiFacetedSearchForm(request.GET)}
