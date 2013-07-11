from django import forms
from django.db.models import get_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

from oscar.apps.address.forms import AbstractAddressForm
from oscar.apps.customer.utils import normalise_email
from oscar.core.compat import get_user_model

User = get_user_model()


class ShippingAddressForm(AbstractAddressForm):

    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)
        self.set_country_queryset()
        self.fields['country'].empty_label = None

    def set_country_queryset(self):
        self.fields['country'].queryset = get_model(
            'address', 'country')._default_manager.filter(
                is_shipping_country=True)

    class Meta:
        model = get_model('order', 'shippingaddress')
        exclude = ('user', 'search_text')


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
                if User._default_manager.filter(email=email).exists():
                    msg = "A user with that email address already exists"
                    self._errors["username"] = self.error_class([msg])
            return self.cleaned_data
        return super(GatewayForm, self).clean()

    def is_guest_checkout(self):
        return self.cleaned_data.get('options', None) == self.GUEST

    def is_new_account_checkout(self):
        return self.cleaned_data.get('options', None) == self.NEW


# The BillingAddress form is in oscar.apps.payment.forms
