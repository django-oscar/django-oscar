from django.conf import settings
from django import forms
from oscar.core.loading import get_model

from oscar.views.generic import PhoneNumberMixin

UserAddress = get_model('address', 'useraddress')


class AbstractAddressForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """
        Set fields in OSCAR_REQUIRED_ADDRESS_FIELDS as required.
        """
        super(AbstractAddressForm, self).__init__(*args, **kwargs)
        field_names = (set(self.fields) &
                       set(settings.OSCAR_REQUIRED_ADDRESS_FIELDS))
        for field_name in field_names:
            self.fields[field_name].required = True


class UserAddressForm(PhoneNumberMixin, AbstractAddressForm):

    class Meta:
        model = UserAddress
        exclude = ('user', 'num_orders', 'hash', 'search_text',
                   'is_default_for_billing', 'is_default_for_shipping')

    def __init__(self, user, *args, **kwargs):
        super(UserAddressForm, self).__init__(*args, **kwargs)
        self.instance.user = user
