from oscar.core.loading import get_class

FacetedSearchView = get_class("search.views.search", "FacetedSearchView")
CatalogueView = get_class("search.views.catalogue", "CatalogueView")
ProductCategoryView = get_class("search.views.catalogue", "ProductCategoryView")
