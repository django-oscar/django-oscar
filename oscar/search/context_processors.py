from oscar.search.forms import MultiFacetedSearchForm

def add_search_form(request):
    '''
    Ensures that the search form is available site wide
    '''
    return {'search_form': MultiFacetedSearchForm(request.GET)}
