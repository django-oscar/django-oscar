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
import_module('basket.forms', ['FormFactory'], locals())
import_module('product.reviews.models', ['ProductReview', 'Vote'], locals())


class CreateProductReviewView(CreateView):
    template_name = "oscar/reviews/add_review.html"
    model = ProductReview
    
    def get_context_data(self, **kwargs):
        context = super(CreateProductReviewView, self).get_context_data(**kwargs)
        context['item'] = get_object_or_404(Item, pk=self.kwargs['item_id'])
        return context
    
    def _get_form_class(self):
        return make_review_form(self.request.user)


class ProductReviewDetailView(DetailView, PostActionMixin):
    """
    Places each review on its own page
    """
    template_name = "oscar/reviews/review.html"
    context_object_name = 'review'
    model = ProductReview
    
    def get_context_data(self, **kwargs):
        context = super(ProductReviewDetailView, self).get_context_data(**kwargs)
        context['item'] = get_object_or_404(Item, pk=self.kwargs['item_id'])
        return context
    
    def do_vote_up(self, review):
        return self.vote_on_review(review, Vote.UP)
    
    def do_vote_down(self, review):
        return self.vote_on_review(review, Vote.DOWN)   
    
    def vote_on_review(self, review, delta):
        user = self.request.user
        self.response = HttpResponseRedirect(review.get_absolute_url())
        if review.user == user:
            messages.info(self.request, "You cannot vote on your own reviews!")
        else:
            try:
                Vote.objects.get(review=review, user=user)
                messages.info(self.request, "You have already voted on this review!") 
            except Vote.DoesNotExist:
                Vote.objects.create(review=review, user=user, delta=delta)
                messages.info(self.request, "Thanks for voting!")   

    
class ProductReviewListView(ListView):
    u"""A list of reviews for a particular product
    * The review browsing page allows reviews to be sorted by score, or recency.
    """    
    template_name = 'oscar/reviews/reviews.html'
    context_object_name = "reviews"
    model = ProductReview
    paginate_by = 20
     
    def get_queryset(self):
        qs = ProductReview.approved.filter(product=self.kwargs['item_id'])
        if 'sort_by' in self.request.GET and self.request.GET['sort_by'] == 'score':
            return qs.order_by('-score')
        return qs.order_by('-date_created')
     
    def get_context_data(self, **kwargs):
        context = super(ProductReviewListView, self).get_context_data(**kwargs)
        context['item'] = get_object_or_404(Item, pk=self.kwargs['item_id'])  
        context['avg_score'] = self.object_list.aggregate(Avg('score'))           
        return context
