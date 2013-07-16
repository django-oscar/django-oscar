from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.models import construct_instance
from django.db.models import get_model

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


class UserAddressForm(AbstractAddressForm):

    class Meta:
        model = UserAddress
        exclude = ('user', 'num_orders', 'hash', 'search_text')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserAddressForm, self).__init__(*args, **kwargs)

    def clean(self):
        # Check this isn't a duplicate of another address
        cleaned_data = super(UserAddressForm, self).clean()
        candidate = construct_instance(
            self, self.instance, self._meta.fields)
        qs = self._meta.model.objects.filter(
            user=self.user,
            hash=candidate.generate_hash())
        if self.instance.id:
            qs = qs.exclude(id=self.instance.id)
        if qs.count() > 0:
            raise forms.ValidationError(_(
                "This address is already in your addressbook"))
        return cleaned_data

    def save(self, commit=True):
        instance = super(UserAddressForm, self).save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance
