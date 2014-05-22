from django.utils.translation import ugettext_lazy as _
from localflavor.us import forms as us_forms

from oscar.apps.checkout import forms as checkout_forms


class ShippingAddressForm(checkout_forms.ShippingAddressForm):
    state = us_forms.USStateField(label="State", widget=us_forms.USStateSelect)

    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)
        self.fields['postcode'].label = _("Zip code")
        self.fields['state'].help_text = _(
            "Only orders going to New Jersey are liable for Sales tax")
