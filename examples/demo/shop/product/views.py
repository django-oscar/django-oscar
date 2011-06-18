from oscar.apps.product.views import ItemDetailView

class MyItemDetailView(ItemDetailView):
    template_name = "product/myitem.html"