from django import forms
from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _

User = get_model('user', 'User')


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_("Email"))
    name = forms.CharField(required=False, label=_("Name"))
