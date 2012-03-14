from django import forms
from django.db.models.loading import get_model

FlatPage = get_model('flatpages', 'FlatPage')


class PageSearchForm(forms.Form):
    title = forms.CharField(required=False, label="Title")


class PageUpdateForm(forms.ModelForm):
    class Meta:
        model = FlatPage
        fields = ('title', 'url', 'content')
