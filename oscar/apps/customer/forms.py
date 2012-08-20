import string
import random

from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from django.core import validators

from oscar.core.loading import get_profile_class


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


class CommonPasswordValidator(validators.BaseValidator):
    # See http://www.smartplanet.com/blog/business-brains/top-20-most-common-passwords-of-all-time-revealed-8216123456-8216princess-8216qwerty/4519
    forbidden_passwords = [
        'password',
        '123456',
        '123456789',
        'iloveyou',
        'princess',
        'monkey',
        'rockyou',
        'babygirl',
        'monkey',
        'qwerty',
        '654321',
    ]
    message = _("Please choose a less common password")
    code = 'password'

    def __init__(self, password_file=None):
        self.limit_value = password_file

    def clean(self, value):
        return value.strip()

    def compare(self, value, limit):
        return value in self.forbidden_passwords

    def get_forbidden_passwords(self):
        if self.limit_value is None:
            return self.forbidden_passwords


class EmailUserCreationForm(forms.ModelForm):
    email = forms.EmailField(label=_('Email Address'))
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput,
                                validators=[validators.MinLengthValidator(6),
                                CommonPasswordValidator()])
    password2 = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

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


class SearchByDateRangeForm(forms.Form):
    date_from = forms.DateField(required=False, label="From")
    date_to = forms.DateField(required=False, label="To")

    def clean(self):
        if self.is_valid() and not self.cleaned_data['date_from'] and not self.cleaned_data['date_to']:
            raise forms.ValidationError(_("At least one date field is required."))
        return super(SearchByDateRangeForm, self).clean()

    def description(self):
        if not self.is_bound or not self.is_valid():
            return 'All orders'
        date_from = self.cleaned_data['date_from']
        date_to = self.cleaned_data['date_to']
        if date_from and date_to:
            return 'Orders placed between %s and %s' % (date_from, date_to)
        elif date_from and not date_to:
            return 'Orders placed since %s' % date_from
        elif not date_from and date_to:
            return 'Orders placed until %s' % date_to

    def get_filters(self):
        date_from = self.cleaned_data['date_from']
        date_to = self.cleaned_data['date_to']
        if date_from and date_to:
            return {'date_placed__range': [date_from, date_to]}
        elif date_from and not date_to:
            return {'date_placed__gt': date_from}
        elif not date_from and date_to:
            return {'date_placed__lt': date_to}
        return {}


class UserForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['instance'] = user
        super(UserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        exclude = ('username', 'password', 'is_staff', 'is_superuser',
                   'is_active', 'last_login', 'date_joined',
                   'user_permissions', 'groups')


if hasattr(settings, 'AUTH_PROFILE_MODULE'):

    Profile = get_profile_class()

    class UserAndProfileForm(forms.ModelForm):

        first_name = forms.CharField(label=_('First name'), max_length=128)
        last_name = forms.CharField(label=_('Last name'), max_length=128)
        email = forms.EmailField(label=_('Email address'))

        # Fields from user model
        user_fields = ('first_name', 'last_name', 'email')

        def __init__(self, user, *args, **kwargs):
            self.user = user
            try:
                instance = user.get_profile()
            except ObjectDoesNotExist:
                # User has no profile, try a blank one
                instance = Profile(user=user)
            kwargs['instance'] = instance

            super(UserAndProfileForm, self).__init__(*args, **kwargs)

            # Add user fields
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

            # Ensure user fields are above profile
            order = list(self.user_fields)
            for field_name in self.fields.keys():
                if field_name not in self.user_fields:
                    order.append(field_name)
            self.fields.keyOrder = order

        class Meta:
            model = Profile
            exclude = ('user',)

        def save(self, *args, **kwargs):
            user = self.instance.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            return super(ProfileForm, self).save(*args,**kwargs)

    ProfileForm = UserAndProfileForm
else:
    ProfileForm = UserForm 
