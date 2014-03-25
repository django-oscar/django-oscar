from django import forms

from oscar.apps.payment import forms as payment_forms


class BillingAddressForm(payment_forms.BillingAddressForm):
    """
    Extended version of the core billing address form that adds a field so
    customers can choose to re-use their shipping address.
    """
    SAME_AS_SHIPPING, NEW_ADDRESS = 'same', 'new'
    CHOICES = (
        (SAME_AS_SHIPPING, 'Use shipping address'),
        (NEW_ADDRESS, 'Enter a new address'),
    )
    same_as_shipping = forms.ChoiceField(
        widget=forms.RadioSelect, choices=CHOICES, initial=SAME_AS_SHIPPING)

    def __init__(self, data=None, *args, **kwargs):
        super(BillingAddressForm, self).__init__(data, *args, **kwargs)

        # If using same address as shipping, we don't need require any of the
        # required billing address fields.
        if data and data.get('same_as_shipping', None) == self.SAME_AS_SHIPPING:
            for field in self.fields:
                if field != 'same_as_shipping':
                    self.fields[field].required = False

    def _post_clean(self):
        # Don't run model validation if using shipping address
        if self.cleaned_data.get('same_as_shipping') == self.SAME_AS_SHIPPING:
            return
        super(BillingAddressForm, self)._post_clean()
