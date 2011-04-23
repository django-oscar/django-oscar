from oscar.apps.search.forms import MultiFacetedSearchForm

def search_form(request):
    '''
    Ensures that the search form is available site wide
    '''
    return {'search_form': MultiFacetedSearchForm(request.GET)}
