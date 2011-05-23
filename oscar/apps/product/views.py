from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView
from django.template.response import TemplateResponse
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages

from oscar.core.loading import import_module
from oscar.apps.reviews.models import ProductReview, Vote
from oscar.apps.reviews.forms import make_review_form, ProductReviewForm

product_models = import_module('product.models', ['Item', 'ItemClass'])
product_signals = import_module('product.signals', ['product_viewed', 'product_search'])
basket_forms = import_module('basket.forms', ['FormFactory'])
history_helpers = import_module('customer.history_helpers', ['receive_product_view'])
review_models = import_module('reviews.models', ['ProductReview', 'Vote'])


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
        product_signals.product_viewed.send(sender=self, product=item, user=request.user, request=request, response=response)
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
            self._item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])
        return self._item
    
    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        context['basket_form'] = self.get_add_to_basket_form()
        # product reviews stuffs
        context['reviews'] = self.get_product_review()
        context['avg_score'] = self.get_avg_review()
        context['review_votes'] = self.get_review_votes()
        return context
    
    def get_add_to_basket_form(self):
        factory = basket_forms.FormFactory()
        return factory.create(self.object)
    
    def get_product_review(self):
        if settings.OSCAR_MODERATE_REVIEWS:        
            return ProductReview.approved_only.all()
        else:
            return ProductReview.objects.all()
    
    def get_avg_review(self):
        if settings.OSCAR_MODERATE_REVIEWS:        
            avg = ProductReview.approved_only.aggregate(Avg('score'))
        else:
            avg = ProductReview.objects.aggregate(Avg('score'))
        return avg['score__avg']
    
    def get_review_votes(self):
        return Vote.objects.all()

    
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


class ProductReviewView(object):
    u"""
    A separate product review page
    * The URL for browsing a products offers should be the normal product URL with /reviews appended at the end
    * The product page shows the average score based on the reviews
    """
    template_name = "oscar/reviews/add_review.html"
    def _is_review_done(self):
        u"""
        Check if the user already reviewed this product
        """                
        try:
            review = review_models.ProductReview.objects.get(product=self.kwargs['item_id'], user=self.request.user.id)
            if review:
                return True
        except ObjectDoesNotExist:                
            return False
    
    def __call__(self, request, *args, **kwargs):        
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.user = self.request.user
        # get the product                
        item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])                
        if (self.user.is_authenticated()) and self._is_review_done():            
            messages.info(self.request, "Your have already reviewed this product!")
            url = item.get_absolute_url()             
            return HttpResponsePermanentRedirect(url) 
        # process request
        if self.request.method == 'POST':        
            review_form = make_review_form(self.user, self.request.POST)            
            if review_form.is_valid():
                if self.user.is_authenticated():
                    review = ProductReview(product=item, user=self.request.user)                   
                elif settings.OSCAR_ALLOW_ANON_REVIEWS:                    
                    review = ProductReview(product=item, user=None, name=self.request.POST['name'], email=self.request.POST['email'])
                else:
                    messages.info(self.request, "Please login to submit a review!")
                    return HttpResponsePermanentRedirect(item.get_absolute_url())
                
                rform = ProductReviewForm(self.request.POST, instance=review)
                rform.save()
                messages.info(self.request, "Your review has been submitted successfully!")
                return HttpResponsePermanentRedirect(item.get_absolute_url())                                                   
        else:            
            review_form = make_review_form(self.request.user)
        
        return render(self.request, self.template_name, {
                    "item" : item,
                    "review_form": review_form,
                    })


class ProductReviewDetailView(DetailView):
    u"""
    Places each review on its own page
    """
    template_name = "oscar/reviews/review.html"
    _review = None
    
    def get(self, request, **kwargs):
        u"""
        Ensures that the correct URL is used
        """
        # get the product review                
        review = self.get_object()        
        correct_path = review.get_absolute_url()
        if correct_path != request.path:
            return HttpResponsePermanentRedirect(correct_path)        
        return super(ProductReviewDetailView, self).get(request, **kwargs)
    
    def get_object(self):
        u"""
        Return a review object
        """
        try:            
            self._review = review_models.ProductReview.objects.get(pk=self.kwargs['review_id'])            
            return self._review
        except ObjectDoesNotExist:                
            raise
    
    def get_context_data(self, **kwargs):
        context = super(ProductReviewDetailView, self).get_context_data(**kwargs)        
        context['review'] = self.get_object()
        return context

    
class ProductReviewListView(ListView):
    u"""A list of reviews for a particular product
    * The review browsing page allows reviews to be sorted by score, or recency.
    """    
    context_object_name = "reviews"
    model = ProductReview
    template_name = 'oscar/reviews/reviews.html'
    paginate_by = 3
     
    def get_queryset(self):
        if 'sort_by' in self.request.GET:
            if self.request.GET['sort_by'] == 'score':
                 self.objects = review_models.ProductReview.top_scored.filter(product=self.kwargs['item_id'])
            elif self.request.GET['sort_by'] == 'recency':
                 self.objects = review_models.ProductReview.recent.filter(product=self.kwargs['item_id'])
        else:
            self.objects = review_models.ProductReview.objects.filter(product=self.kwargs['item_id'])
        return self.objects 
     
    def get_context_data(self, **kwargs):
        context = super(ProductReviewListView, self).get_context_data(**kwargs)
        item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])    
        context['item'] = item
        context['avg_score'] = self.objects.aggregate(Avg('score'))           
        return context


class ProductReviewVoteView(object):
    u"""Processes voting of product reviews
    """
    
    template_name = "oscar/product/detail.html"   
    
    def _is_vote_done(self):
        u"""
        Check if the user already reviewed this product
        """                
        try:
            vote = review_models.Vote.objects.get(review=self.kwargs['review_id'])
            if vote:
                return True
        except ObjectDoesNotExist:                
            return False
    
    def __call__(self, request, *args, **kwargs):        
        self.request = request
        self.args = args
        self.kwargs = kwargs
        template_name = "oscar/product/detail.html" 
        # get the product                    
        item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])
        review = get_object_or_404(review_models.ProductReview, pk=self.kwargs['review_id'])
        if self.request.method == 'POST':
            if self._is_vote_done():
                messages.info(self.request, "Your have already voted for this product!")         
                return HttpResponsePermanentRedirect(item.get_absolute_url()) 
            else:                                
                vote = Vote.objects.create(review=review, user=self.request.user, choice=0)                        
                if self.request.POST['action'] == 'voteup':
                    vote.choice = 1                    
                elif self.request.POST['action'] == 'votedown':
                    vote.choice = -1
                vote.save()
                messages.info(self.request, "Your vote has been submitted successfully!")
                return HttpResponsePermanentRedirect(item.get_absolute_url())                                                   
        reviews = review_models.ProductReview.approved_only.filter(product=self.kwargs['item_id'])
        return render(self.request, template_name, {
                    "item" : item,
                    "reviews": reviews,
                    })
