from django.views import generic
from django.db.models import get_model

Product = get_model('catalogue', 'Product')


class ProductListView(generic.ListView):
    template_name = 'dashboard/catalogue/product_list.html'
    model = Product
    context_object_name = 'products'
    paginate_by = 20


class ProductUpdateView(generic.UpdateView):
    template_name = 'dashboard/catalogue/product_update.html'
    model = Product
    context_object_name = 'product'


