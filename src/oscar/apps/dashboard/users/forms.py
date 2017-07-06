from django import forms
from django.utils.translation import ugettext_lazy as _, pgettext_lazy


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_("Email"))
    name = forms.CharField(
        required=False, label=pgettext_lazy(u"User's name", u"Name"))
