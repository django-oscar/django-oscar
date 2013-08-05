from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib import messages
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_classes
from oscar.apps.catalogue.reviews.signals import review_added

ProductReviewForm, VoteForm = get_classes(
    'catalogue.reviews.forms', ['ProductReviewForm', 'VoteForm'])
Vote = get_model('reviews', 'vote')
ProductReview = get_model('reviews', 'ProductReview')
Product = get_model('catalogue', 'product')


class CreateProductReview(CreateView):
    template_name = "catalogue/reviews/review_form.html"
    model = get_model('reviews', 'productreview')
    product_model = get_model('catalogue', 'product')
    form_class = ProductReviewForm
    view_signal = review_added

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            self.product_model, pk=kwargs['product_pk'])
        if self.product.has_review_by(request.user):
            messages.warning(
                self.request, _("You have already reviewed this product!"))
            return HttpResponseRedirect(self.product.get_absolute_url())
        return super(CreateProductReview, self).dispatch(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = super(CreateProductReview, self).post(
            request, *args, **kwargs)
        if self.object:
            self.send_signal(request, response, self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super(CreateProductReview, self).get_context_data(**kwargs)
        context['product'] = self.product
        return context

    def get_form_kwargs(self):
        kwargs = super(CreateProductReview, self).get_form_kwargs()
        review = self.model(product=self.product)
        if self.request.user.is_authenticated():
            review.user = kwargs['user'] = self.request.user
        kwargs['instance'] = review
        return kwargs

    def get_success_url(self):
        messages.success(
            self.request, _("Thank you for reviewing this product"))
        return self.product.get_absolute_url()

    def send_signal(self, request, response, review):
        self.view_signal.send(sender=self, review=review, user=request.user,
                              request=request, response=response)


class ProductReviewDetail(DetailView):
    template_name = "catalogue/reviews/review_detail.html"
    context_object_name = 'review'
    model = ProductReview

    def get_context_data(self, **kwargs):
        context = super(ProductReviewDetail, self).get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            Product, pk=self.kwargs['product_pk'])
        return context


class AddVoteView(View):

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        review = get_object_or_404(ProductReview, pk=self.kwargs['pk'])
        if not review.user_may_vote(request.user):
            if review.user == request.user:
                error = _("You cannot vote on your own reviews")
            elif review.votes.filter(user=request.user).exists():
                error =  _("You have already voted on this review")
            else:
                error = _("We couldn't process your vote")
            messages.error(request, error)
        else:
            vote = Vote(user=request.user, review=review)
            form = VoteForm(request.POST, instance=vote)
            if form.is_valid():
                form.save()
                messages.success(request, _("Thanks for voting!"))
            else:
                messages.error(request, _("We couldn't process your vote"))
        return HttpResponseRedirect(
            request.META.get('HTTP_REFERER', product.get_absolute_url()))


class ProductReviewList(ListView):
    """
    Browse reviews for a product
    """
    template_name = 'catalogue/reviews/review_list.html'
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
        context['product'] = get_object_or_404(
            self.product_model, pk=self.kwargs['product_pk'])
        return context
