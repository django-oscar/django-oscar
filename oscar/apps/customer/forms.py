import string
import random

from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib.auth.models import User

def generate_username():
    uname = ''.join([random.choice(string.letters + string.digits + '_') for i in range(30)]) 
    
    try:
        User.objects.get(username=uname)
        return generate_username()
    except User.DoesNotExist:
        return uname


class EmailAuthenticationForm(AuthenticationForm):
    """
    Extends the standard django AuthenticationForm, to support 75 character
    usernames. 75 character usernames are needed to support the EmailOrUsername
    auth backend.
    """
    username = forms.EmailField(label=_('Email Address'))


class EmailUserCreationForm(forms.ModelForm):
    email = forms.EmailField(label=_('Email Address'))
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('email', )
        
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(_("A user with that email address already exists."))
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')
        
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
    
    def save(self, commit=True):
        user = super(EmailUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.username = generate_username()
        
        if commit:
            user.save()
        return user
