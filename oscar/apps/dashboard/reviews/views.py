from django.db.models import get_model
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.views.generic import ListView, UpdateView

from oscar.views.generic import BulkEditMixin
from oscar.apps.dashboard.reviews import forms

ProductReview = get_model('reviews', 'productreview')


class ReviewListView(ListView, BulkEditMixin):
    model = ProductReview
    template_name = 'dashboard/reviews/review_list.html'
    context_object_name = 'review_list'
    form_class = forms.ReviewSearchForm
    base_description = 'All reviews'
    paginate_by = 25
    current_view = 'dashboard:reviews-list'
    actions = ('update_selected_review_status',)
    checkbox_object_name = 'review'

    def get_queryset(self):
        return ProductReview.objects.all()

    def get(self, request, **kwargs):
        return super(self.__class__, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(self.__class__, self).post(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['review_form'] = forms.DashboardProductReviewForm()
        return context

    def update_selected_review_status(self, request, reviews):
        """
        Update the status of the selected *reviews* with the new
        status in the *request* POST data. Redirects back to the
        list view of reviews.
        """
        new_status = int(request.POST.get('status'))
        for review in reviews:
            review.status = new_status
            review.save()
        return HttpResponseRedirect(reverse('dashboard:reviews-list'))


class ReviewUpdateView(UpdateView):
    model = ProductReview
    template_name = 'dashboard/reviews/review_update.html'
    form_class = forms.DashboardProductReviewForm

    def get_success_url(self):
        return reverse('dashboard:reviews-list')
