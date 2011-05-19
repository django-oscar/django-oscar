from oscar.apps.product import ProductApplication
from shop.product.views import MyItemDetailView

app = ProductApplication(detail_view=MyItemDetailView)