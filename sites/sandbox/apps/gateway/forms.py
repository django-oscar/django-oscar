from django import forms
from django.contrib.auth.models import User

from oscar.apps.customer.utils import normalise_email


class GatewayForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = normalise_email(self.cleaned_data['email'])
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A user already exists with email %s" % email
            )
        return email
