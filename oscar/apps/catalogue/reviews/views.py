from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Avg
from django.contrib import messages
from oscar.apps.catalogue.reviews.forms import SignedInUserProductReviewForm, AnonymousUserProductReviewForm, VoteForm
from django.db.models import get_model

vote_model = get_model('reviews', 'vote')


class CreateProductReview(CreateView):
    template_name = "reviews/add_review.html"
    model = get_model('reviews', 'productreview')
    product_model = get_model('catalogue', 'product')
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
        return super(CreateProductReview, self).get(request, *args, **kwargs)        
    
    def get_context_data(self, **kwargs):
        context = super(CreateProductReview, self).get_context_data(**kwargs)
        context['product'] = self.get_product()
        return context
    
    def get_product(self):
        return get_object_or_404(self.product_model, pk=self.kwargs['product_pk'])
    
    def get_form_class(self):
        if not self.request.user.is_authenticated():
            return self.anonymous_review_form
        return self.review_form
    
    def get_form_kwargs(self):
        kwargs = super(CreateProductReview, self).get_form_kwargs()
        review = self.model(product=self.get_product())
        if self.request.user.is_authenticated():
            review.user = self.request.user
        kwargs['instance'] = review
        return kwargs
    
    def get_success_url(self):
        return self.object.product.get_absolute_url()


class CreateProductReviewComplete(DetailView):
    template_name = "reviews/add_review_complete.html"
    context_object_name = 'review'
    model = get_model('reviews', 'productreview')
    product_model = get_model('catalogue', 'product')
    
    def get_context_data(self, **kwargs):
        context = super(CreateProductReviewComplete, self).get_context_data(**kwargs)
        context['product'] = get_object_or_404(self.product_model, pk=self.kwargs['product_pk'])
        return context    


class ProductReviewDetail(DetailView):
    """
    Places each review on its own page
    """
    
    template_name = "reviews/review.html"
    context_object_name = 'review'
    model = get_model('reviews', 'productreview')
    product_model = get_model('catalogue', 'product')
    vote_model = vote_model
    
    def get_context_data(self, **kwargs):
        context = super(ProductReviewDetail, self).get_context_data(**kwargs)
        context['product'] = get_object_or_404(self.product_model, pk=self.kwargs['product_pk'])
        return context
    
    def post(self, request, *args, **kwargs ):
        review = self.get_object()
        try:
            vote = self.vote_model.objects.get(user=request.user, review=review)
        except self.vote_model.DoesNotExist:
            vote = self.vote_model(user=request.user, review=review)
        form = VoteForm(request.POST,instance=vote)

        if form.is_valid():
            form.save()
            messages.info(request, "Thanks for voting!")
        else:
            messages.info(request, "We couldn't process your vote")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER',review.get_absolute_url()))

    
class ProductReviewList(ListView):
    u"""A list of reviews for a particular product
    * The review browsing page allows reviews to be sorted by score, or recency.
    """    
    template_name = 'reviews/reviews.html'
    context_object_name = "reviews"
    model = get_model('reviews', 'productreview')
    product_model = get_model('catalogue', 'product')    
    paginate_by = 20
     
    def get_queryset(self):
        qs = self.model.approved.filter(product=self.kwargs['product_pk'])
        if 'sort_by' in self.request.GET and self.request.GET['sort_by'] == 'score':
            return qs.order_by('-score')
        return qs.order_by('-date_created')
     
    def get_context_data(self, **kwargs):
        context = super(ProductReviewList, self).get_context_data(**kwargs)
        context['product'] = get_object_or_404(self.product_model, pk=self.kwargs['product_pk'])  
        context['avg_score'] = self.object_list.aggregate(Avg('score'))           
        return context
