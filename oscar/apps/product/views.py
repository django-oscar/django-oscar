from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView, CreateView
from django.template.response import TemplateResponse
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages

from oscar.view.generic import PostActionMixin
from oscar.core.loading import import_module
import_module('product.models', ['Item', 'ItemClass'], locals())
import_module('product.signals', ['product_viewed', 'product_search'], locals())
import_module('basket.forms', ['FormFactory'], locals())
import_module('customer.history_helpers', ['receive_product_view'], locals())
import_module('product.reviews.models', ['ProductReview', 'Vote'], locals())


class ItemDetailView(DetailView):
    u"""View a single product."""
    template_folder = "oscar/product"
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
        product_viewed.send(sender=self, product=item, user=request.user, request=request, response=response)
        return response;
    
    def get_template_names(self):
        """
        Returns a list of possible templates.
        
        We try 2 options before defaulting to oscar/product/detail.html:
        1). detail-for-upc-<upc>.html
        2). detail-for-class-<classname>.html
        
        This allows alternative templates to be provided for a per-product
        and a per-item-class basis.
        """    
        product = self.get_object()
        names = ['%s/detail-for-upc-%s.html' % (self.template_folder, product.upc), 
                 '%s/detail-for-class-%s.html' % (self.template_folder, product.item_class.name.lower()),
                 '%s/detail.html' % (self.template_folder)]
        return names
    
    def get_object(self):
        u"""
        Return a product object or a 404.
        
        We cache the object as this method gets called twice."""
        if not self._item:
            self._item = get_object_or_404(Item, pk=self.kwargs['item_id'])
        return self._item
    
    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        context['basket_form'] = self.get_add_to_basket_form()
        context['reviews'] = self.get_reviews()
        return context
    
    def get_add_to_basket_form(self):
        factory = FormFactory()
        return factory.create(self.object)
    
    def get_reviews(self):
        return ProductReview.approved.filter(product=self.get_object())
    
    
class ItemClassListView(ListView):
    u"""View products filtered by item-class."""
    context_object_name = "products"
    template_name = 'oscar/product/browse.html'
    paginate_by = 20

    def get_queryset(self):
        item_class = get_object_or_404(ItemClass, slug=self.kwargs['item_class_slug'])
        return Item.browsable.filter(item_class=item_class)


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
            product_search.send(sender=self, query=q, user=self.request.user)
            
            return Item.browsable.filter(title__icontains=q)
        else:
            return Item.browsable.all()
        
    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        q = self.get_search_query()
        if not q:
            context['summary'] = 'All products'
        else:
            context['summary'] = "Products matching '%s'" % q
            context['search_term'] = q
        return context
