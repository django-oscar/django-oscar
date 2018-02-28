import datetime

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from oscar.core.loading import get_classes, get_model
from oscar.core.utils import format_datetime
from oscar.views import sort_queryset
from oscar.views.generic import BulkEditMixin

ProductReviewSearchForm, DashboardProductReviewForm = \
    get_classes('dashboard.reviews.forms', ('ProductReviewSearchForm', 'DashboardProductReviewForm'))
ProductReview = get_model('reviews', 'productreview')


class ReviewListView(BulkEditMixin, generic.ListView):
    model = ProductReview
    template_name = 'dashboard/reviews/review_list.html'
    context_object_name = 'review_list'
    form_class = ProductReviewSearchForm
    review_form_class = DashboardProductReviewForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    actions = ('update_selected_review_status',)
    checkbox_object_name = 'review'
    desc_template = _("%(main_filter)s %(date_filter)s %(status_filter)s"
                      "%(kw_filter)s %(name_filter)s")

    def get(self, request, *args, **kwargs):
        response = super(ReviewListView, self).get(request, **kwargs)
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
        if queryset is None:
            queryset = self.model.objects.all()

        if date_from:
            queryset = queryset.filter(date_created__gte=date_from)
            self.desc_ctx['date_filter'] \
                = _(" created after %s") % format_datetime(date_from)
        if date_to:
            # Add 24 hours to make search inclusive
            date_to = date_to + datetime.timedelta(days=1)
            queryset = queryset.filter(date_created__lt=date_to)
            self.desc_ctx['date_filter'] \
                = _(" created before %s") % format_datetime(date_to)

        if date_from and date_to:
            # override description
            self.desc_ctx['date_filter'] \
                = _(" created between %(start_date)s and %(end_date)s") % {
                    'start_date': format_datetime(date_from),
                    'end_date': format_datetime(date_to)}
        return queryset

    def get_queryset(self):
        queryset = self.model.objects.select_related('product', 'user').all()
        queryset = sort_queryset(
            queryset, self.request, ['score', 'total_votes', 'date_created'])
        self.desc_ctx = {
            'main_filter': _('All reviews'),
            'date_filter': '',
            'status_filter': '',
            'kw_filter': '',
            'name_filter': '',
        }

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        queryset = self.add_filter_status(queryset, data['status'])
        queryset = self.add_filter_keyword(queryset, data['keyword'])
        queryset = self.add_filter_name(queryset, data['name'])

        queryset = self.get_date_from_to_queryset(
            data['date_from'], data['date_to'], queryset)

        return queryset

    def add_filter_status(self, queryset, status):
        # checking for empty string rather then True is required
        # as zero is a valid value for 'status' but would be
        # evaluated to False
        if status != '':
            queryset = queryset.filter(status=status).distinct()
            display_status = self.form.get_friendly_status()
            self.desc_ctx['status_filter'] \
                = _(" with status matching '%s'") % display_status
        return queryset

    def add_filter_keyword(self, queryset, keyword):
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(body__icontains=keyword)
            ).distinct()
            self.desc_ctx['kw_filter'] \
                = _(" with keyword matching '%s'") % keyword
        return queryset

    def add_filter_name(self, queryset, name):
        if name:
            # If the value is two words, then assume they are first name and
            # last name
            parts = name.split()
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
            self.desc_ctx['name_filter'] \
                = _(" with customer name matching '%s'") % name

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ReviewListView, self).get_context_data(**kwargs)
        context['review_form'] = self.review_form_class()
        context['form'] = self.form
        context['description'] = self.desc_template % self.desc_ctx
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
    form_class = DashboardProductReviewForm
    context_object_name = 'review'

    def get_success_url(self):
        return reverse('dashboard:reviews-list')


class ReviewDeleteView(generic.DeleteView):
    model = ProductReview
    template_name = 'dashboard/reviews/review_delete.html'
    context_object_name = 'review'

    def get_success_url(self):
        return reverse('dashboard:reviews-list')
