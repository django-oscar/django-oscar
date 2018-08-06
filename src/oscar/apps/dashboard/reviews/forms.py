from django import forms
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model, get_class


ProductReview = get_model('reviews', 'productreview')
DatePickerInput = get_class('oscar.forms.widgets', 'DatePickerInput')


class DashboardProductReviewForm(forms.ModelForm):
    choices = (
        (ProductReview.APPROVED, _('Approved')),
        (ProductReview.REJECTED, _('Rejected')),
    )
    status = forms.ChoiceField(choices=choices, label=_("Status"))

    class Meta:
        model = ProductReview
        fields = ('title', 'body', 'score', 'status')


class ProductReviewSearchForm(forms.Form):
    STATUS_CHOICES = (
        ('', '------------'),
    ) + ProductReview.STATUS_CHOICES
    keyword = forms.CharField(required=False, label=_("Keyword"))
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES,
                               label=_("Status"))
    date_from = forms.DateTimeField(required=False, label=_("Date from"),
                                    widget=DatePickerInput)
    date_to = forms.DateTimeField(required=False, label=_('to'),
                                  widget=DatePickerInput)
    name = forms.CharField(required=False, label=_('Customer name'))

    def get_friendly_status(self):
        raw = int(self.cleaned_data['status'])
        for key, value in self.STATUS_CHOICES:
            if key == raw:
                return value
        return ''
