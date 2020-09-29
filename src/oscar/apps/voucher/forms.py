from django import forms
from django.utils.translation import gettext_lazy as _


class BasketVoucherForm(forms.Form):
    code = forms.CharField(max_length=128, label=_('Code'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()