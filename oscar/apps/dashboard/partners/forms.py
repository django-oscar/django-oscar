from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model
from django import forms
from oscar.apps.customer.forms import EmailUserCreationForm, CommonPasswordValidator
from django.core import validators


Partner = get_model('partner', 'Partner')


class PartnerSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Partner name"))


class PartnerCreateForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ('name',)


class NewUserForm(EmailUserCreationForm):

    def __init__(self, partner, *args, **kwargs):
        self.partner = partner
        super(NewUserForm, self).__init__(*args, **kwargs)

    def save(self):
        user = super(EmailUserCreationForm, self).save(commit=False)
        user.is_staff = True
        user.save()
        self.partner.users.add(user)
        return user

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


class ExistingUserForm(forms.ModelForm):
    """
    Slightly different form that makes
    * makes saving password optional
    * doesn't regenerate username
    * doesn't allow changing email till #668 is resolved
    """
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput,
        required=False,
        validators=[validators.MinLengthValidator(6),
                    CommonPasswordValidator()])
    password2 = forms.CharField(
        required=False,
        label=_('Confirm Password'),
        widget=forms.PasswordInput)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')

        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        user = super(ExistingUserForm, self).save(commit=False)
        if self.cleaned_data['password1']:
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'password1', 'password2')


class UserEmailForm(forms.Form):
    email = forms.CharField(max_length=100)
