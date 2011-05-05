from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView

from oscar.core.loading import import_module

product_models = import_module('product.models', ['Item', 'ItemClass'])
product_signals = import_module('product.signals', ['product_viewed', 'product_search'])
basket_forms = import_module('basket.forms', ['FormFactory'])
history_helpers = import_module('customer.history_helpers', ['receive_product_view'])


class ItemDetailView(DetailView):
    u"""View a single product."""
    template_name = "oscar/product/item.html"
    _item = None
    
    def get(self, request, **kwargs):
        u"""
        Ensures that the correct URL is used
        """
        item = self.get_object()
        correct_path = item.get_absolute_url() 
        if correct_path != request.path:
            return HttpResponsePermanentRedirect(correct_path)
        
        response = super(ItemDetailView, self).get(request, **kwargs)
        
        # Send signal to record the view of this product
        product_signals.product_viewed.send(sender=self, product=item, user=request.user, request=request, response=response)
        return response;
    
    def get_object(self):
        u"""
        Return a product object or a 404.
        
        We cache the object as this method gets called twice."""
        if not self._item:
            self._item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])
        return self._item
    
    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        context['basket_form'] = self.get_add_to_basket_form()
        return context
    
    def get_add_to_basket_form(self):
        factory = basket_forms.FormFactory()
        return factory.create(self.object)
    
class ItemClassListView(ListView):
    u"""View products filtered by item-class."""
    context_object_name = "products"
    template_name = 'oscar/product/browse.html'
    paginate_by = 20

    def get_queryset(self):
        item_class = get_object_or_404(product_models.ItemClass, slug=self.kwargs['item_class_slug'])
        return product_models.Item.browsable.filter(item_class=item_class)


class ProductListView(ListView):
    u"""A list of products"""
    context_object_name = "products"
    template_name = 'oscar/product/browse.html'
    paginate_by = 20

    def get_search_query(self):
        u"""Return a search query from GET"""
        q = None
        if 'q' in self.request.GET and self.request.GET['q']:
            q = self.request.GET['q'].strip()
        return q

    def get_queryset(self):
        u"""Return a set of prodcuts"""
        q = self.get_search_query()
        if q:
            # Send signal to record the view of this product
            product_signals.product_search.send(sender=self, query=q, user=self.request.user)
            
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
