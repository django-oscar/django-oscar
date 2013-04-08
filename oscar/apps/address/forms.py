from django.conf import settings
from django.forms import ModelForm
from django.db.models import get_model

UserAddress = get_model('address', 'useraddress')

class AbstractAddressForm(ModelForm):

    def __init__(self, *args, **kwargs):
        """
        Set fields in OSCAR_REQUIRED_ADDRESS_FIELDS as required.
        """
        super(AbstractAddressForm, self).__init__(*args, **kwargs)
        field_names = (set(self.fields) &
                       set(settings.OSCAR_REQUIRED_ADDRESS_FIELDS))
        for field_name in field_names:
            self.fields[field_name].required = True


class UserAddressForm(AbstractAddressForm):

    class Meta:
        model = UserAddress
        exclude = ('user', 'num_orders', 'hash', 'search_text')
