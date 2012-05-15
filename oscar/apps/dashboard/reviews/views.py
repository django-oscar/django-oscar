import datetime

from django.views import generic
from django.db.models import get_model, Q
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.template.defaultfilters import date as format_date

from oscar.views.generic import BulkEditMixin
from oscar.apps.dashboard.reviews import forms

ProductReview = get_model('reviews', 'productreview')


class ReviewListView(generic.ListView, BulkEditMixin):
    model = ProductReview
    template_name = 'dashboard/reviews/review_list.html'
    context_object_name = 'review_list'
    form_class = forms.ProductReviewSearchForm
    review_form_class = forms.DashboardProductReviewForm
    paginate_by = 25
    current_view = 'dashboard:reviews-list'
    actions = ('update_selected_review_status',)
    checkbox_object_name = 'review'
    base_description = 'All reviews'

    def get(self, request, *args, **kwargs):
        response = super(self.__class__, self).get(request, **kwargs)
        self.form = self.form_class()
        return response

    def get_date_from_to_queryset(self, date_from, date_to, queryset=None):
        """
        Get a ``QuerySet`` of ``ProductReview`` items that match the time
        frame specified by *date_from* and *date_to*. Both parameters are
        expected to be in ``datetime`` format with *date_from* < *date_to*.
        If *queryset* is specified, it will be filtered according to the
        given dates. Otherwise, a new queryset for all ``ProductReview``
        items is created.
        """
        if not queryset:
            self.model.objects.all()

        if date_from and date_to:
            # Add 24 hours to make search inclusive
            date_to = date_to + datetime.timedelta(days=1)
            queryset = queryset.filter(
                date_created__gte=date_from
            ).filter(
                date_created__lt=date_to
            )
            self.description += " created between %s and %s" % (
                format_date(date_from),
                format_date(date_to)
            )

        elif date_from:
            queryset = queryset.filter(date_created__gte=date_from)
            self.description += " created after %s" % format_date(date_from)

        elif date_to:
            # Add 24 hours to make search inclusive
            date_to = date_to + datetime.timedelta(days=1)
            queryset = queryset.filter(date_created__lt=date_to)
            self.description += " created before %s" % format_date(date_to)

        return queryset

    def get_queryset(self):
        queryset = self.model.objects.all()
        self.description = self.base_description

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        # checking for empty string rather then True is required
        # as zero is a valid value for 'status' but would be
        # evaluated to False
        if data['status'] != '':
            queryset = queryset.filter(status=data['status']).distinct()
            self.description += " with status matching '%s'" % data['status']

        if data['keyword']:
            queryset = queryset.filter(
                Q(title__icontains=data['keyword']) |
                Q(body__icontains=data['keyword'])
            ).distinct()
            self.description += " with keyword matching '%s'" % data['keyword']

        queryset = self.get_date_from_to_queryset(data['date_from'],
                                                  data['date_to'], queryset)

        if data['name']:
            # If the value is two words, then assume they are first name and
            # last name
            parts = data['name'].split()
            if len(parts) >= 2:
                queryset = queryset.filter(
                    user__first_name__istartswith=parts[0],
                    user__last_name__istartswith=parts[1]
                ).distinct()
            else:
                queryset = queryset.filter(
                    Q(user__first_name__istartswith=parts[0]) |
                    Q(user__last_name__istartswith=parts[-1])
                ).distinct()
            self.description += " with customer name matching '%s'" % data['name']

        return queryset

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['review_form'] = self.review_form_class()
        context['form'] = self.form
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


class ReviewUpdateView(generic.UpdateView):
    model = ProductReview
    template_name = 'dashboard/reviews/review_update.html'
    form_class = forms.DashboardProductReviewForm

    def get_success_url(self):
        return reverse('dashboard:reviews-list')


class ReviewDeleteView(generic.DeleteView):
    model = ProductReview
    template_name = 'dashboard/reviews/review_delete.html'
    context_object_name = 'review'

    def get_success_url(self):
        return reverse('dashboard:reviews-list')
