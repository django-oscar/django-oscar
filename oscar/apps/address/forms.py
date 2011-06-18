from django.forms import ModelForm
from django.db.models import get_model

UserAddress = get_model('address', 'useraddress')


class UserAddressForm(ModelForm):

    class Meta:
        model = UserAddress
        exclude = ('user', 'num_orders', 'hash', 'search_text')
    