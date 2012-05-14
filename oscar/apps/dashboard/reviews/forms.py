from django import forms
from django.db.models import get_model


class DashboardProductReviewForm(forms.ModelForm):
    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'body', 'score', 'status')


class ReviewSearchForm(forms.Form):
    pass
