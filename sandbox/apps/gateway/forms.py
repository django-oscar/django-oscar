from django import forms
from django.contrib.auth.models import User


class GatewayForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(
                "A user already exists with email %s" % email
            )
        return email
