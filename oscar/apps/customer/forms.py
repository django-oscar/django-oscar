import string
import random

from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.db.models import get_model
from django.contrib.auth.models import User
from django.contrib.auth import forms as auth_forms
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.http import int_to_base36
from django.contrib.sites.models import get_current_site
from django.contrib.auth.tokens import default_token_generator

from oscar.core.loading import get_profile_class, get_class

Dispatcher = get_class('customer.utils', 'Dispatcher')
CommunicationEventType = get_model('customer', 'communicationeventtype')
ProductAlert = get_model('customer', 'ProductAlert')


def generate_username():
    uname = ''.join([random.choice(string.letters + string.digits + '_') for i in range(30)])
    try:
        User.objects.get(username=uname)
        return generate_username()
    except User.DoesNotExist:
        return uname


class PasswordResetForm(auth_forms.PasswordResetForm):
    communication_type_code = "PASSWORD_RESET"

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, **kwargs):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        site = get_current_site(request)
        if domain_override is not None:
            site.domain = site.name = domain_override
        for user in self.users_cache:
            # Build reset url
            reset_url = "%s://%s%s" % (
                'https' if use_https else 'http',
                site.domain,
                reverse('password-reset-confirm', kwargs={
                    'uidb36': int_to_base36(user.id),
                    'token': token_generator.make_token(user)}))
            ctx = {
                'site': site,
                'reset_url': reset_url}
            messages = CommunicationEventType.objects.get_and_render(
                code=self.communication_type_code, context=ctx)
            Dispatcher().dispatch_user_messages(user, messages)


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
        '1234',
        '12345'
        '123456',
        '123456y',
        '123456789',
        'iloveyou',
        'princess',
        'monkey',
        'rockyou',
        'babygirl',
        'monkey',
        'qwerty',
        '654321',
        'dragon',
        'pussy',
        'baseball',
        'football',
        'letmein',
        'monkey',
        '696969',
        'abc123',
        'qwe123',
        'qweasd',
        'mustang',
        'michael',
        'shadow',
        'master',
        'jennifer',
        '111111',
        '2000',
        'jordan',
        'superman'
        'harley'
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
        email = self.cleaned_data['email'].lower()
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


class CleanEmailMixin(object):

    def clean_email(self):
        """
        Make sure that the email address is aways unique as it is
        used instead of the username. This is necessary because the
        unique-ness of email addresses is *not* enforced on the model
        level in ``django.contrib.auth.models.User``.
        """
        email = self.cleaned_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # this email address is unique so we don't have to worry
            # about it
            return email

        if self.instance and self.instance.id != user.id:
            raise ValidationError(
                _("A user with this email address already exists")
            )

        return email


class UserForm(forms.ModelForm, CleanEmailMixin):

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

    class UserAndProfileForm(forms.ModelForm, CleanEmailMixin):

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


class ProductAlertForm(forms.ModelForm):
    email = forms.EmailField(required=True, label=_(u'Send notification to'),
                             widget=forms.TextInput(attrs={
                                 'placeholder': _('Enter your email')
                             }))

    def __init__(self, user, product, *args, **kwargs):
        self.user = user
        self.product = product
        super(ProductAlertForm, self).__init__(*args, **kwargs)

        # Only show email field to unauthenticated users
        if user and user.is_authenticated():
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].required = False

    def save(self, commit=True):
        alert = super(ProductAlertForm, self).save(commit=False)
        if self.user.is_authenticated():
            alert.user = self.user
        alert.product = self.product
        if commit:
            alert.save()
        return alert

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data.get('email')
        if email:
            try:
                ProductAlert.objects.get(
                    product=self.product, email=email,
                    status=ProductAlert.ACTIVE)
            except ProductAlert.DoesNotExist:
                pass
            else:
                raise forms.ValidationError(_(
                    "There is already an active stock alert for %s") % email)
        elif self.user.is_authenticated():
            try:
                ProductAlert.objects.get(product=self.product,
                                         user=self.user,
                                         status=ProductAlert.ACTIVE)
            except ProductAlert.DoesNotExist:
                pass
            else:
                raise forms.ValidationError(_(
                    "You already have an active alert for this product"))
        return cleaned_data

    class Meta:
        model = ProductAlert
        exclude = ('user', 'key',
                   'status', 'date_confirmed', 'date_cancelled', 'date_closed',
                   'product')
