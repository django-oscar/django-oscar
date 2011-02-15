from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView

from oscar.services import import_module

product_models = import_module('product.models', ['Item', 'ItemClass'])
basket_forms = import_module('basket.forms', ['FormFactory'])


class ItemDetailView(DetailView):
    """
    View a single product.
    """
    template_name = "product/item.html"
    
    def get(self, request, **kwargs):
        item = self.get_object()
        correct_path = item.get_absolute_url() 
        if correct_path != request.path:
            return HttpResponsePermanentRedirect(correct_path)
        return super(ItemDetailView, self).get(request, **kwargs)
    
    def get_object(self):
        return get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])
    
    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        
        # Add add-to-basket form for this product
        factory = basket_forms.FormFactory()
        context['form'] = factory.create(self.object)
        
        return context


class ItemClassListView(ListView):
    """
    View products filtered by item-class.
    """
    context_object_name = "products"
    template_name = 'product/browse.html'
    paginate_by = 20

    def get_queryset(self):
        item_class = get_object_or_404(product_models.ItemClass, slug=self.kwargs['item_class_slug'])
        return product_models.Item.browsable.filter(item_class=item_class)


class ProductListView(ListView):

    context_object_name = "products"
    template_name = 'product/browse.html'
    paginate_by = 20

    def get_search_query(self):
        q = None
        if 'q' in self.request.GET and self.request.GET['q']:
            q = self.request.GET['q'].strip()
        return q

    def get_queryset(self):
        q = self.get_search_query()
        if q:
            return product_models.Item.browsable.filter(title__icontains=q)
        else:
            return product_models.Item.browsable.all()
        
    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        q = self.get_search_query()
        if not q:
            context['summary'] = 'All products'
        else:
            context['summary'] = "Products matching '%s'" % q
            context['search_term'] = q
        return context
