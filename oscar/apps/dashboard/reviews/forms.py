from django import forms
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

ProductReview = get_model('reviews', 'productreview')


class DashboardProductReviewForm(forms.ModelForm):
    choices= (
        (ProductReview.APPROVED, _('Approved')),
        (ProductReview.REJECTED, _('Rejected')),
    )
    status = forms.ChoiceField(choices=choices, label=_("Status"))

    class Meta:
        model = ProductReview
        fields = ('title', 'body', 'score', 'status')


class ProductReviewSearchForm(forms.Form):
    STATUS_CHOICES = (
        ('', _('------------')),
    ) + ProductReview.STATUS_CHOICES
    keyword = forms.CharField(required=False, label=_("Keyword"))
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES, label=_("Status"))
    date_from = forms.DateTimeField(required=False, label=_("from"))
    date_to = forms.DateTimeField(required=False, label=_('to'))
    name = forms.CharField(required=False, label=_("Name"))
