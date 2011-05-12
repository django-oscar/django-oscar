from random import randint
from sys import maxint
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render, get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.models import User

from oscar.services import import_module
from oscar.views import ModelView
from oscar.reviews.models import ProductReview, Vote
from oscar.reviews.forms import make_review_form, make_voting_form, ProductReviewForm

product_models = import_module('product.models', ['Item', 'ItemClass'])
product_signals = import_module('product.signals', ['product_viewed'])
basket_forms = import_module('basket.forms', ['FormFactory'])
review_models = import_module('reviews.models', ['ProductReview', 'Vote'])


class ItemDetailView(DetailView):
    u"""View a single product."""
    template_name = "product/item.html"
    _item = None
    
    def get(self, request, **kwargs):
        u"""
        Ensures that the correct URL is used
        """
        item = self.get_object()
        correct_path = item.get_absolute_url() 
        if correct_path != request.path:
            return HttpResponsePermanentRedirect(correct_path)
        
        # Send signal to record the view of this product
        product_signals.product_viewed.send(sender=self, product=item, user=self.request.user)
        
        return super(ItemDetailView, self).get(request, **kwargs)
    
    def get_object(self):
        u"""
        Return a product object or a 404.
        
        We cache the object as this method gets called twice."""
        if not self._item:
            self._item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])
        return self._item
    
    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        context['form'] = self.get_add_to_basket_form()
        context['reviews'] = self.get_product_review()
        context['avg_score'] = self.get_avg_review()
        context['review_votes'] = self.get_review_votes()
        context['up_vote_form'] = self.get_voting_form('up', self.request.POST)
        context['down_vote_form'] = self.get_voting_form('down', self.request.POST)        
        return context
    
    def get_product_review(self):
        if settings.OSCAR_MODERATE_REVIEWS:        
            return ProductReview.objects.filter(approved=True)
        else:
            return ProductReview.objects.all()
    
    def get_avg_review(self):
        if settings.OSCAR_MODERATE_REVIEWS:        
            avg = ProductReview.objects.filter(approved=True).aggregate(Avg('score'))
        else:
            avg = ProductReview.objects.aggregate(Avg('score'))
        return avg['score__avg']
        
    
    def get_add_to_basket_form(self):
        factory = basket_forms.FormFactory()
        return factory.create(self.object)

    def get_review_votes(self):
        return Vote.objects.all()

    def get_voting_form(self, choice, values):       
        if self.request.method == 'POST':            
            if self.request.POST['upvote']:
               print "Got up vote"
            elif self.request.POST['downvote']:
               print "got down vote"
        else:
           voting_form = make_voting_form(choice, values)
        return voting_form


class ItemClassListView(ListView):
    u"""View products filtered by item-class."""
    context_object_name = "products"
    template_name = 'product/browse.html'
    paginate_by = 20

    def get_queryset(self):
        item_class = get_object_or_404(product_models.ItemClass, slug=self.kwargs['item_class_slug'])
        return product_models.Item.browsable.filter(item_class=item_class)


class ProductListView(ListView):
    u"""A list of products"""
    context_object_name = "products"
    template_name = 'product/browse.html'
    paginate_by = 20

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
    """
  
    def _is_review_done(self):
        u"""
        Check if the user already reviewed this product
        """                
        try:
            review = review_models.ProductReview.objects.get(product=self.kwargs['item_id'], user=self.request.user.id)
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
        if self._is_review_done():
            messages.info(self.request, "Your have already reviewed this product!")
            url = item.get_absolute_url()             
            return HttpResponsePermanentRedirect(url) 
                                     
        template_name = "reviews/add_review.html"
                        
        if self.request.method == 'POST':        
            review_form = make_review_form(self.user, self.request.POST)            
            if review_form.is_valid():
                if self.user.is_authenticated():
                    review = ProductReview(product=item, user=self.request.user)                   
                elif settings.OSCAR_ALLOW_ANON_REVIEWS:                    
                    review = ProductReview(product=item, user=None)
                else:
                    messages.info(self.request, "Please login to submit a review!")
                    return HttpResponsePermanentRedirect(item.get_absolute_url())
                
                rform = ProductReviewForm(self.request.POST, instance=review)
                rform.save()
                messages.info(self.request, "Your review has been submitted successfully!")
                return HttpResponsePermanentRedirect(item.get_absolute_url())                                                   
        else:            
            review_form = make_review_form(self.request.user)
        
        return render(self.request, template_name, {
                    "item" : item,
                    "review_form": review_form,
                    })

class ProductReviewDetailView(DetailView):
    u"""
    Places each review on its own page
    """
    template_name = "reviews/review.html"
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
        return super(ReviewDetailView, self).get(request, **kwargs)
    
    def get_object(self):
        u"""
        Return a review object or a 404.
        """
        try:            
            self._review = review_models.ProductReview.objects.get(pk=self.kwargs['review_id'])
            return self._review
        except ObjectDoesNotExist:                
            raise
    
    def get_context_data(self, **kwargs):
        context = super(ReviewDetailView, self).get_context_data(**kwargs)        
        context['review'] = self.get_object()
        return context
    
class ProductReviewListView(ListView):
    u"""A list of reviews for a particular product"""    
    context_object_name = "reviews"
    model = ProductReview
    template_name = 'reviews/reviews.html'
    paginate_by = 20
     
    def get_queryset(self):
        self.objects = review_models.ProductReview.objects.filter(product=self.kwargs['item_id'])
        return self.objects 
     
    def get_context_data(self, **kwargs):
        context = super(ReviewListView, self).get_context_data(**kwargs)
        item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])    
        context['item'] = item
        context['avg_score'] = self.objects.aggregate(Avg('score'))           
        return context
    
class ProductReviewVoteView(object):
    u"""Processes voting of product reviews
    """
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
        template_name = "product/item.html"
        print self.request.user   
        # get the product                
        item = get_object_or_404(product_models.Item, pk=self.kwargs['item_id'])
        review = get_object_or_404(review_models.ProductReview, pk=self.kwargs['review_id'], user=self.request.user)
        if self.request.method == 'POST':
            if self._is_vote_done():
                messages.info(self.request, "Your have already voted for this product!")         
                return HttpResponsePermanentRedirect(item.get_absolute_url()) 
            else:                                
                vote = Vote.objects.create(review=review, user=self.request.user)
                print vote
                #assert False                
                if self.request.POST['action'] == 'voteup':
                    vote.up = 1
                elif self.request.POST['action'] == 'votedown':
                    vote.down = 1
                vote.save()
                messages.info(self.request, "Your vote has been submitted successfully!")
                return HttpResponsePermanentRedirect(item.get_absolute_url())                                                   
        reviews = review_models.ProductReviews.objects.get(product=self.kwargs['item_id'])
        return render(self.request, template_name, {
                    "item" : item,
                    "reviews": reviews,
                    })
