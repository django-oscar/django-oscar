from django.http import HttpResponsePermanentRedirect, Http404
from django.views.generic import ListView, DetailView
from django.db.models import get_model

from oscar.apps.catalogue.signals import product_viewed, product_search

product_model = get_model('catalogue','product')
category_model = get_model('catalogue', 'category')


class ProductDetailView(DetailView):
    context_object_name = 'product'
    model = product_model
    view_signal = product_viewed
    template_folder = "catalogue"
    _product = None
    
    def get_object(self):
        if not self._product:
            self._product = super(ProductDetailView, self).get_object()
        return self._product
    
    def get(self, request, **kwargs):
        """
        Ensure that the correct URL is used
        """
        product = self.get_object()
        correct_path = product.get_absolute_url() 
        if correct_path != request.path:
            return HttpResponsePermanentRedirect(correct_path)
        response = super(ProductDetailView, self).get(request, **kwargs)
        
        # Send signal to record the view of this product
        self.view_signal.send(sender=self, product=product, user=request.user, request=request, response=response)
        return response;

    def get_template_names(self):
        """
        Return a list of possible templates.
        
        We try 2 options before defaulting to catalogue/detail.html:
        1). detail-for-upc-<upc>.html
        2). detail-for-class-<classname>.html
        
        This allows alternative templates to be provided for a per-product
        and a per-item-class basis.
        """    
        product = self.get_object()
        names = ['%s/detail-for-upc-%s.html' % (self.template_folder, product.upc), 
                 '%s/detail-for-class-%s.html' % (self.template_folder, product.product_class.name.lower()),
                 '%s/detail.html' % (self.template_folder)]
        return names


class ProductCategoryView(ListView):
    u"""A list of products"""
    context_object_name = "products"
    template_name = 'catalogue/browse.html'
    paginate_by = 20
    
    def get_categories(self):
        slug = self.kwargs['category_slug']
        try:
            category = category_model.objects.get(slug=slug)
        except category_model.DoesNotExist:
            raise Http404()
        categories = list(category.get_descendants())
        categories.append(category)
        return categories
    
    def get_context_data(self, **kwargs):
        context = super(ProductCategoryView, self).get_context_data(**kwargs)

        categories = self.get_categories()

        context['categories'] = categories
        context['category'] = categories[-1]
        context['summary'] = categories[-1].name
        return context    

    def get_queryset(self):
        return product_model.browsable.filter(categories__in=self.get_categories()).distinct()


class ProductListView(ListView):
    u"""A list of products"""
    context_object_name = "products"
    template_name = 'catalogue/browse.html'
    paginate_by = 20
    search_signal = product_search

    def get_search_query(self):
        u"""Return a search query from GET"""
        q = None
        if 'q' in self.request.GET and self.request.GET['q']:
            q = self.request.GET['q'].strip()
        return q

    def get_queryset(self):
        u"""Return a set of products"""
        q = self.get_search_query()
        if q:
            # Send signal to record the view of this product
            self.search_signal.send(sender=self, query=q, user=self.request.user)
            return product_model.browsable.filter(title__icontains=q)
        else:
            return product_model.browsable.all()
        
    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        q = self.get_search_query()
        if not q:
            context['summary'] = 'All products'
        else:
            context['summary'] = "Products matching '%s'" % q
            context['search_term'] = q
        return context
