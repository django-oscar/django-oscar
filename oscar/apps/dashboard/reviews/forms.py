from django import forms
from django.db.models import get_model

ProductReview = get_model('reviews', 'productreview')



class DashboardProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ('title', 'body', 'score', 'status')


class ProductReviewSearchForm(forms.Form):
    keyword = forms.CharField(required=False)
    status = forms.ChoiceField(required=False, choices=ProductReview.STATUS_CHOICES)
    date_from = forms.DateTimeField(required=False)
    date_to = forms.DateTimeField(required=False, label='to')
    name = forms.CharField(required=False)
