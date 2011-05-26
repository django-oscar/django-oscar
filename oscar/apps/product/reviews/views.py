from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Avg
from django.contrib import messages

from oscar.view.generic import PostActionMixin
from oscar.apps.product.reviews.forms import SignedInUserProductReviewForm, AnonymousUserProductReviewForm

from django.db.models import get_model

class CreateProductReviewView(CreateView):
    template_name = "reviews/add_review.html"
    model = get_model('reviews', 'productreview')
    product_model = get_model('product', 'item')
    review_form = SignedInUserProductReviewForm
    anonymous_review_form = AnonymousUserProductReviewForm
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            product = self.get_product()
            try:
                self.model.objects.get(user=request.user, product=product)
                messages.info(self.request, "You have already reviewed this product!")
                return HttpResponseRedirect(product.get_absolute_url()) 
            except self.model.DoesNotExist:
                pass
        return super(CreateProductReviewView, self).get(request, *args, **kwargs)        
    
    def get_context_data(self, **kwargs):
        context = super(CreateProductReviewView, self).get_context_data(**kwargs)
        context['item'] = self.get_product()
        return context
    
    def get_product(self):
        return get_object_or_404(self.product_model, pk=self.kwargs['item_pk'])
    
    def get_form_class(self):
        if not self.request.user.is_authenticated():
            return self.anonymous_review_form
        return self.review_form
    
    def get_form_kwargs(self):
        kwargs = super(CreateProductReviewView, self).get_form_kwargs()
        review = self.model(product=self.get_product())
        if self.request.user.is_authenticated():
            review.user = self.request.user
        kwargs['instance'] = review
        return kwargs
    
    def get_success_url(self):
        return self.object.product.get_absolute_url()


class ProductReviewDetailView(DetailView, PostActionMixin):
    """
    Places each review on its own page
    """
    template_name = "reviews/review.html"
    context_object_name = 'review'
    model = get_model('reviews', 'productreview')
    product_model = get_model('product', 'item')
    vote_model = get_model('reviews', 'vote')
    
    def get_context_data(self, **kwargs):
        context = super(ProductReviewDetailView, self).get_context_data(**kwargs)
        context['item'] = get_object_or_404(self.product_model, pk=self.kwargs['item_id'])
        return context
    
    def do_vote_up(self, review):
        return self.vote_on_review(review, self.vote_model.UP)
    
    def do_vote_down(self, review):
        return self.vote_on_review(review, self.vote_model.DOWN)   
    
    def vote_on_review(self, review, delta):
        user = self.request.user
        self.response = HttpResponseRedirect(review.product.get_absolute_url())
        if review.user == user:
            messages.info(self.request, "You cannot vote on your own reviews!")
        else:
            try:
                self.vote_model.objects.get(review=review, user=user)
                messages.info(self.request, "You have already voted on this review!") 
            except self.vote_model.DoesNotExist:
                self.vote_model.objects.create(review=review, user=user, delta=delta)
                messages.info(self.request, "Thanks for voting!")   

    
class ProductReviewListView(ListView):
    u"""A list of reviews for a particular product
    * The review browsing page allows reviews to be sorted by score, or recency.
    """    
    template_name = 'reviews/reviews.html'
    context_object_name = "reviews"
    model = get_model('reviews', 'productreview')
    product_model = get_model('product', 'item')    
    paginate_by = 20
     
    def get_queryset(self):
        qs = self.model.approved.filter(product=self.kwargs['item_pk'])
        if 'sort_by' in self.request.GET and self.request.GET['sort_by'] == 'score':
            return qs.order_by('-score')
        return qs.order_by('-date_created')
     
    def get_context_data(self, **kwargs):
        context = super(ProductReviewListView, self).get_context_data(**kwargs)
        context['item'] = get_object_or_404(self.product_model, pk=self.kwargs['item_pk'])  
        context['avg_score'] = self.object_list.aggregate(Avg('score'))           
        return context
