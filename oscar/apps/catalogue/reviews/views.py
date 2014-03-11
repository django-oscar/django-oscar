from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib import messages
from oscar.core.loading import get_model
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
    model = get_model('reviews', 'ProductReview')
    product_model = get_model('catalogue', 'product')
    form_class = ProductReviewForm
    view_signal = review_added

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            self.product_model, pk=kwargs['product_pk'])
        # check permission to leave review
        if not self.product.is_review_permitted(request.user):
            if self.product.has_review_by(request.user):
                message = _("You have already reviewed this product!")
            else:
                message = _("You can't leave a review for this product.")
            messages.warning(self.request, message)
            return HttpResponseRedirect(self.product.get_absolute_url())

        return super(CreateProductReview, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateProductReview, self).get_context_data(**kwargs)
        context['product'] = self.product
        return context

    def get_form_kwargs(self):
        kwargs = super(CreateProductReview, self).get_form_kwargs()
        kwargs['product'] = self.product
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super(CreateProductReview, self).form_valid(form)
        self.send_signal(self.request, response, self.object)
        return response

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
    """
    Simple view for voting on a review.

    We use the URL path to determine the product and review and use a 'delta'
    POST variable to indicate it the vote is up or down.
    """

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        review = get_object_or_404(ProductReview, pk=self.kwargs['pk'])

        form = VoteForm(review, request.user, request.POST)
        if form.is_valid():
            if form.is_up_vote:
                review.vote_up(request.user)
            elif form.is_down_vote:
                review.vote_down(request.user)
            messages.success(request, _("Thanks for voting!"))
        else:
            for error_list in form.errors.values():
                for msg in error_list:
                    messages.error(request, msg)
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
        if 'sort_by' in self.request.GET \
                and self.request.GET['sort_by'] == 'score':
            return qs.order_by('-score')
        return qs.order_by('-date_created')

    def get_context_data(self, **kwargs):
        context = super(ProductReviewList, self).get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            self.product_model, pk=self.kwargs['product_pk'])
        return context
