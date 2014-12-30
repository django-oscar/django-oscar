
from oscar.core.loading import get_class, get_model
from oscar.views.generic import PhoneNumberMixin

UserAddress = get_model('address', 'useraddress')

AbstractAddressForm = get_class('address.abstract_forms', 'AbstractAddressForm')


class UserAddressForm(PhoneNumberMixin, AbstractAddressForm):

    class Meta:
        model = UserAddress
        exclude = ('user', 'num_orders', 'hash', 'search_text',
                   'is_default_for_billing', 'is_default_for_shipping')

    def __init__(self, user, *args, **kwargs):
        super(UserAddressForm, self).__init__(*args, **kwargs)
        self.instance.user = user
