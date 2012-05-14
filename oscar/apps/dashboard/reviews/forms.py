from django import forms
from django.db.models import get_model


class DashboardProductReviewForm(forms.ModelForm):
    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'body', 'score', 'status')


class ProductReviewSearchForm(forms.Form):
    keyword = forms.CharField(required=False)
    date_from = forms.DateTimeField(required=False)
    date_to = forms.DateTimeField(required=False, label='to')
    name = forms.CharField(required=False)
