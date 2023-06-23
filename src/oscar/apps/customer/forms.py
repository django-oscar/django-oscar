import datetime
import string

from django import forms
from django.conf import settings
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.apps.customer.utils import get_password_reset_url, normalise_email
from oscar.core.compat import existing_user_fields, get_user_model
from oscar.core.loading import get_class, get_model, get_profile_class
from oscar.core.utils import datetime_combine
from oscar.forms import widgets

CustomerDispatcher = get_class("customer.utils", "CustomerDispatcher")
ProductAlert = get_model("customer", "ProductAlert")
User = get_user_model()


def generate_username():
    letters = string.ascii_letters
    allowed_chars = letters + string.digits + "_"
    uname = get_random_string(length=30, allowed_chars=allowed_chars)
    try:
        User.objects.get(username=uname)
        return generate_username()
    except User.DoesNotExist:
        return uname


class PasswordResetForm(auth_forms.PasswordResetForm):
    """
    This form takes the same structure as its parent from :py:mod:`django.contrib.auth`
    """

    def save(self, *args, domain_override=None, request=None, **kwargs):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        site = get_current_site(request)
        if domain_override is not None:
            site.domain = site.name = domain_override
        for user in self.get_users(self.cleaned_data["email"]):
            self.send_password_reset_email(site, user, request)

    def send_password_reset_email(self, site, user, request=None):
        extra_context = {
            "user": user,
            "site": site,
            "reset_url": get_password_reset_url(user),
            "request": request,
        }
        CustomerDispatcher().send_password_reset_email_for_user(user, extra_context)


class EmailAuthenticationForm(AuthenticationForm):
    """
    Extends the standard django AuthenticationForm, to support 75 character
    usernames. 75 character usernames are needed to support the EmailOrUsername
    authentication backend.
    """

    username = forms.EmailField(label=_("Email address"))
    redirect_url = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, host, *args, **kwargs):
        self.host = host
        super().__init__(*args, **kwargs)

    def clean_redirect_url(self):
        url = self.cleaned_data["redirect_url"].strip()
        if url and url_has_allowed_host_and_scheme(url, self.host):
            return url


class ConfirmPasswordForm(forms.Form):
    """
    Extends the standard django AuthenticationForm, to support 75 character
    usernames. 75 character usernames are needed to support the EmailOrUsername
    authentication backend.
    """

    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(_("The entered password is not valid!"))
        return password


class EmailUserCreationForm(forms.ModelForm):
    email = forms.EmailField(label=_("Email address"))
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirm password"), widget=forms.PasswordInput)
    redirect_url = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, host=None, **kwargs):
        self.host = host
        super().__init__(*args, **kwargs)

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get("password2")
        # Validate after self.instance is updated with form data
        # otherwise validators can't access email
        # see django.contrib.auth.forms.UserCreationForm
        if password:
            try:
                validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error("password2", error)

    def clean_email(self):
        """
        Checks for existing users with the supplied email address.
        """
        email = normalise_email(self.cleaned_data["email"])
        if User._default_manager.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _("A user with that email address already exists")
            )
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data.get("password2", "")
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def clean_redirect_url(self):
        url = self.cleaned_data["redirect_url"].strip()
        if url and url_has_allowed_host_and_scheme(url, self.host):
            return url
        return settings.LOGIN_REDIRECT_URL

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if "username" in [f.name for f in User._meta.fields]:
            user.username = generate_username()
        if commit:
            user.save()
        return user


class OrderSearchForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label=pgettext_lazy("start date", "From"),
        widget=widgets.DatePickerInput(),
    )
    date_to = forms.DateField(
        required=False,
        label=pgettext_lazy("end date", "To"),
        widget=widgets.DatePickerInput(),
    )
    order_number = forms.CharField(required=False, label=_("Order number"))

    def clean(self):
        if self.is_valid() and not any(
            [
                self.cleaned_data["date_from"],
                self.cleaned_data["date_to"],
                self.cleaned_data["order_number"],
            ]
        ):
            raise forms.ValidationError(_("At least one field is required."))
        return super().clean()

    def description(self):
        """
        Uses the form's data to build a useful description of what orders
        are listed.
        """
        if not self.is_bound or not self.is_valid():
            return _("All orders")
        else:
            date_from = self.cleaned_data["date_from"]
            date_to = self.cleaned_data["date_to"]
            order_number = self.cleaned_data["order_number"]
            return self._orders_description(date_from, date_to, order_number)

    def _orders_description(self, date_from, date_to, order_number):
        if date_from and date_to:
            if order_number:
                desc = _(
                    "Orders placed between %(date_from)s and "
                    "%(date_to)s and order number containing "
                    "%(order_number)s"
                )
            else:
                desc = _("Orders placed between %(date_from)s and% (date_to)s")
        elif date_from:
            if order_number:
                desc = _(
                    "Orders placed since %(date_from)s and "
                    "order number containing %(order_number)s"
                )
            else:
                desc = _("Orders placed since %(date_from)s")
        elif date_to:
            if order_number:
                desc = _(
                    "Orders placed until %(date_to)s and "
                    "order number containing %(order_number)s"
                )
            else:
                desc = _("Orders placed until %(date_to)s")
        elif order_number:
            desc = _("Orders with order number containing %(order_number)s")
        else:
            return None
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "order_number": order_number,
        }
        return desc % params

    def get_filters(self):
        date_from = self.cleaned_data["date_from"]
        date_to = self.cleaned_data["date_to"]
        order_number = self.cleaned_data["order_number"]
        kwargs = {}
        if date_from:
            kwargs["date_placed__gte"] = datetime_combine(date_from, datetime.time.min)
        if date_to:
            kwargs["date_placed__lte"] = datetime_combine(date_to, datetime.time.max)
        if order_number:
            kwargs["number__contains"] = order_number
        return kwargs


class UserForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs["instance"] = user
        super().__init__(*args, **kwargs)
        if "email" in self.fields:
            self.fields["email"].required = True

    def clean_email(self):
        """
        Make sure that the email address is always unique as it is
        used instead of the username. This is necessary because the
        uniqueness of email addresses is *not* enforced on the model
        level in ``django.contrib.auth.models.User``.
        """
        email = normalise_email(self.cleaned_data["email"])
        if (
            User._default_manager.filter(email__iexact=email)
            .exclude(id=self.user.id)
            .exists()
        ):
            raise ValidationError(_("A user with this email address already exists"))
        # Save the email unaltered
        return email

    class Meta:
        model = User
        fields = existing_user_fields(["first_name", "last_name", "email"])


Profile = get_profile_class()
if Profile:

    class UserAndProfileForm(forms.ModelForm):
        def __init__(self, user, *args, **kwargs):
            try:
                instance = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                # User has no profile, try a blank one
                instance = Profile(user=user)
            kwargs["instance"] = instance

            super().__init__(*args, **kwargs)

            # Get profile field names to help with ordering later
            profile_field_names = list(self.fields.keys())

            # Get user field names (we look for core user fields first)
            core_field_names = set([f.name for f in User._meta.fields])
            user_field_names = ["email"]
            for field_name in ("first_name", "last_name"):
                if field_name in core_field_names:
                    user_field_names.append(field_name)
            user_field_names.extend(User._meta.additional_fields)

            # Store user fields so we know what to save later
            self.user_field_names = user_field_names

            # Add additional user form fields
            additional_fields = forms.fields_for_model(User, fields=user_field_names)
            self.fields.update(additional_fields)

            # Ensure email is required and initialised correctly
            self.fields["email"].required = True

            # Set initial values
            for field_name in user_field_names:
                self.fields[field_name].initial = getattr(user, field_name)

            # Ensure order of fields is email, user fields then profile fields
            self.field_order = user_field_names + profile_field_names
            self.order_fields(self.field_order)

        class Meta:
            model = Profile
            # pylint: disable=modelform-uses-exclude
            exclude = ("user",)

        def clean_email(self):
            email = normalise_email(self.cleaned_data["email"])

            users_with_email = User._default_manager.filter(
                email__iexact=email
            ).exclude(id=self.instance.user.id)
            if users_with_email.exists():
                raise ValidationError(
                    _("A user with this email address already exists")
                )
            return email

        def save(self, *args, **kwargs):
            user = self.instance.user

            # Save user also
            for field_name in self.user_field_names:
                setattr(user, field_name, self.cleaned_data[field_name])
            user.save()

            return super().save(*args, **kwargs)

    ProfileForm = UserAndProfileForm
else:
    ProfileForm = UserForm


class ProductAlertForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label=_("Send notification to"),
        widget=forms.TextInput(attrs={"placeholder": _("Enter your email")}),
    )

    def __init__(self, user, product, *args, **kwargs):
        self.user = user
        self.product = product
        super().__init__(*args, **kwargs)

        # Only show email field to unauthenticated users
        if user and user.is_authenticated:
            self.fields["email"].widget = forms.HiddenInput()
            self.fields["email"].required = False

    def save(self, commit=True):
        alert = super().save(commit=False)
        if self.user.is_authenticated:
            alert.user = self.user
        alert.product = self.product
        if commit:
            alert.save()
        return alert

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data.get("email")
        if email:
            try:
                ProductAlert.objects.get(
                    product=self.product,
                    email__iexact=email,
                    status=ProductAlert.ACTIVE,
                )
            except ProductAlert.DoesNotExist:
                pass
            else:
                raise forms.ValidationError(
                    _("There is already an active stock alert for %s") % email
                )

            # Check that the email address hasn't got other unconfirmed alerts.
            # If they do then we don't want to spam them with more until they
            # have confirmed or cancelled the existing alert.
            if ProductAlert.objects.filter(
                email__iexact=email, status=ProductAlert.UNCONFIRMED
            ).count():
                raise forms.ValidationError(
                    _(
                        "%s has been sent a confirmation email for another product "
                        "alert on this site. Please confirm or cancel that request "
                        "before signing up for more alerts."
                    )
                    % email
                )
        elif self.user.is_authenticated:
            try:
                ProductAlert.objects.get(
                    product=self.product, user=self.user, status=ProductAlert.ACTIVE
                )
            except ProductAlert.DoesNotExist:
                pass
            else:
                raise forms.ValidationError(
                    _("You already have an active alert for this product")
                )
        return cleaned_data

    class Meta:
        model = ProductAlert
        fields = ["email"]
