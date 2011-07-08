from oscar.apps.catalogue.views import ItemDetailView

class MyItemDetailView(ItemDetailView):
    template_name = "product/myitem.html"