from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

from oscar.apps.address.forms import AbstractAddressForm
from oscar.apps.customer.utils import normalise_email
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.views.generic import PhoneNumberMixin

User = get_user_model()
Country = get_model('address', 'Country')


class ShippingAddressForm(PhoneNumberMixin, AbstractAddressForm):

    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)
        self.adjust_country_field()

    def adjust_country_field(self):
        countries = Country._default_manager.filter(
            is_shipping_country=True)

        # No need to show country dropdown if there is only one option
        if len(countries) == 1:
            self.fields.pop('country', None)
            self.instance.country = countries[0]
        else:
            self.fields['country'].queryset = countries
            self.fields['country'].empty_label = None

    class Meta:
        model = get_model('order', 'shippingaddress')
        fields = [
            'title', 'first_name', 'last_name',
            'line1', 'line2', 'line3', 'line4',
            'state', 'postcode', 'country',
            'phone_number', 'notes',
        ]


class GatewayForm(AuthenticationForm):
    username = forms.EmailField(label=_("My email address is"))
    GUEST, NEW, EXISTING = 'anonymous', 'new', 'existing'
    CHOICES = (
        (GUEST, _('I am a new customer and want to checkout as a guest')),
        (NEW, _('I am a new customer and want to create an account '
                'before checking out')),
        (EXISTING, _('I am a returning customer, and my password is')))
    options = forms.ChoiceField(widget=forms.widgets.RadioSelect,
                                choices=CHOICES, initial=GUEST)

    def clean_username(self):
        return normalise_email(self.cleaned_data['username'])

    def clean(self):
        if self.is_guest_checkout() or self.is_new_account_checkout():
            if 'password' in self.errors:
                del self.errors['password']
            if 'username' in self.cleaned_data:
                email = normalise_email(self.cleaned_data['username'])
                if User._default_manager.filter(email__iexact=email).exists():
                    msg = "A user with that email address already exists"
                    self._errors["username"] = self.error_class([msg])
            return self.cleaned_data
        return super(GatewayForm, self).clean()

    def is_guest_checkout(self):
        return self.cleaned_data.get('options', None) == self.GUEST

    def is_new_account_checkout(self):
        return self.cleaned_data.get('options', None) == self.NEW


# The BillingAddress form is in oscar.apps.payment.forms
