from django import forms
from django.db.models.loading import get_model

User = get_model('user', 'User')


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label="Email")
    name = forms.CharField(required=False, label="Name")
