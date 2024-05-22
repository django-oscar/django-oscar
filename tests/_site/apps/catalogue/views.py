from oscar.apps.catalogue.views import ProductDetailView as OscarProductDetailView


class ParentProductDetailView(OscarProductDetailView):
    enforce_parent = True
    enforce_paths = False
