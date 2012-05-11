from django.db.models import get_model
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.template.response import TemplateResponse
from django.views.generic import ListView, UpdateView

from oscar.apps.dashboard.reviews.forms import DashboardProductReviewForm

ProductReview = get_model('reviews', 'productreview')


class ReviewListView(ListView):
    template_name = 'dashboard/reviews/review_list.html'
    context_object_name = 'review_list'

    def get_queryset(self):
        return ProductReview.objects.all()


class ReviewUpdateView(UpdateView):
    model = ProductReview
    template_name = 'dashboard/reviews/review_update.html'
    form_class = DashboardProductReviewForm 
