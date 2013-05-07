from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Avg
from django.contrib import messages
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_classes
from oscar.apps.catalogue.reviews.signals import review_added

SignedInUserProductReviewForm, AnonymousUserProductReviewForm, VoteForm = get_classes(
    'catalogue.reviews.forms', ['SignedInUserProductReviewForm', 'AnonymousUserProductReviewForm', 'VoteForm'])
Vote = get_model('reviews', 'vote')


class CreateProductReview(CreateView):
    template_name = "catalogue/reviews/review_form.html"
    model = get_model('reviews', 'productreview')
    product_model = get_model('catalogue', 'product')
    review_form = SignedInUserProductReviewForm
    anonymous_review_form = AnonymousUserProductReviewForm
    view_signal = review_added

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            product = self.get_product()
            try:
                self.model.objects.get(user=request.user, product=product)
                messages.warning(
                    self.request, _("You have already reviewed this product!"))
                return HttpResponseRedirect(product.get_absolute_url())
            except self.model.DoesNotExist:
                pass
        return super(CreateProductReview, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = super(CreateProductReview, self).post(request, *args, **kwargs)
        if self.object:
            self.send_signal(request, response, self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super(CreateProductReview, self).get_context_data(**kwargs)
        context['product'] = self.get_product()
        return context

    def get_product(self):
        return get_object_or_404(
            self.product_model, pk=self.kwargs['product_pk'])

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
        messages.success(
            self.request, _("Thank you for reviewing this product"))
        return self.object.product.get_absolute_url()

    def send_signal(self, request, response, review):
        self.view_signal.send(sender=self, review=review, user=request.user,
                              request=request, response=response)


class ProductReviewDetail(DetailView):
    template_name = "catalogue/reviews/review_detail.html"
    context_object_name = 'review'
    model = get_model('reviews', 'productreview')
    product_model = get_model('catalogue', 'product')

    def get_context_data(self, **kwargs):
        context = super(ProductReviewDetail, self).get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            self.product_model, pk=self.kwargs['product_pk'])
        return context

    def post(self, request, *args, **kwargs):
        review = self.get_object()
        response = HttpResponseRedirect(
            request.META.get('HTTP_REFERER', review.get_absolute_url()))
        if review.user == request.user:
            messages.error(request, _("You cannot vote on your own reviews"))
            return response

        try:
            vote = Vote.objects.get(user=request.user, review=review)
        except Vote.DoesNotExist:
            vote = Vote(user=request.user, review=review)
        else:
            messages.error(request, _("You have already voted on this review"))
            return response

        form = VoteForm(request.POST, instance=vote)
        if form.is_valid():
            form.save()
            messages.success(request, _("Thanks for voting!"))
        else:
            messages.error(request, _("We couldn't process your vote"))
        return response


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
