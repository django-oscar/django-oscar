from oscar.core.loading import get_class

PriceRangeSearchForm = get_class('search.forms', 'PriceRangeSearchForm')


def search_form(request):
    """
    Ensure that the search form is available site wide
    """
    return {'search_form': PriceRangeSearchForm(request.GET)}
