from oscar.core.loading import get_class

CatalogueSearchForm = get_class('catalogue.forms', 'CatalogueSearchForm')


def search_form(request):
    """
    Ensure that the search form is available site wide
    """
    return {'search_form': CatalogueSearchForm(request.GET)}
