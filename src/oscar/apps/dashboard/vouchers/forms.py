from django import forms
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model
from oscar.forms import widgets

Voucher = get_model('voucher', 'Voucher')
VoucherSet = get_model('voucher', 'VoucherSet')
Benefit = get_model('offer', 'Benefit')
Range = get_model('offer', 'Range')


class VoucherForm(forms.Form):
    """
    A specialised form for creating a voucher and offer
    model.
    """
    name = forms.CharField(label=_("Name"))
    code = forms.CharField(label=_("Code"))

    start_datetime = forms.DateTimeField(
        widget=widgets.DateTimePickerInput(),
        label=_("Start datetime"))
    end_datetime = forms.DateTimeField(
        widget=widgets.DateTimePickerInput(),
        label=_("End datetime"))

    usage = forms.ChoiceField(choices=Voucher.USAGE_CHOICES, label=_("Usage"))

    benefit_range = forms.ModelChoiceField(
        label=_('Which products get a discount?'),
        queryset=Range.objects.all(),
    )
    type_choices = (
        (Benefit.PERCENTAGE, _('Percentage off of products in range')),
        (Benefit.FIXED, _('Fixed amount off of products in range')),
        (Benefit.SHIPPING_PERCENTAGE,
         _("Discount is a percentage off of the shipping cost")),
        (Benefit.SHIPPING_ABSOLUTE,
         _("Discount is a fixed amount of the shipping cost")),
        (Benefit.SHIPPING_FIXED_PRICE, _("Get shipping for a fixed price")),
    )
    benefit_type = forms.ChoiceField(
        choices=type_choices,
        label=_('Discount type'),
    )
    benefit_value = forms.DecimalField(
        label=_('Discount value'))

    exclusive = forms.BooleanField(
        required=False,
        label=_("Exclusive offers cannot be combined on the same items"))

    def __init__(self, voucher=None, *args, **kwargs):
        self.voucher = voucher
        super(VoucherForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            voucher = Voucher.objects.get(name=name)
        except Voucher.DoesNotExist:
            pass
        else:
            if (not self.voucher) or (voucher.id != self.voucher.id):
                raise forms.ValidationError(_("The name '%s' is already in"
                                              " use") % name)
        return name

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        if not code:
            raise forms.ValidationError(_("Please enter a voucher code"))
        try:
            voucher = Voucher.objects.get(code=code)
        except Voucher.DoesNotExist:
            pass
        else:
            if (not self.voucher) or (voucher.id != self.voucher.id):
                raise forms.ValidationError(_("The code '%s' is already in"
                                              " use") % code)
        return code

    def clean(self):
        cleaned_data = super(VoucherForm, self).clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        if start_datetime and end_datetime and end_datetime < start_datetime:
            raise forms.ValidationError(_("The start date must be before the"
                                          " end date"))
        return cleaned_data


class VoucherSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Name"))
    code = forms.CharField(required=False, label=_("Code"))
    is_active = forms.BooleanField(required=False, label=_("Is Active?"))
    in_set = forms.BooleanField(
        required=False, label=_("In Voucherset?"))

    def clean_code(self):
        return self.cleaned_data['code'].upper()


class VoucherSetForm(forms.ModelForm):
    class Meta:
        model = VoucherSet
        fields = [
            'name',
            'code_length',
            'description',
            'start_datetime',
            'end_datetime',
            'count',
        ]
        widgets = {
            'start_datetime': widgets.DateTimePickerInput(),
            'end_datetime': widgets.DateTimePickerInput(),
        }

    benefit_range = forms.ModelChoiceField(
        label=_('Which products get a discount?'),
        queryset=Range.objects.all(),
    )
    type_choices = (
        (Benefit.PERCENTAGE, _('Percentage off of products in range')),
        (Benefit.FIXED, _('Fixed amount off of products in range')),
        (Benefit.SHIPPING_PERCENTAGE,
         _("Discount is a percentage off of the shipping cost")),
        (Benefit.SHIPPING_ABSOLUTE,
         _("Discount is a fixed amount of the shipping cost")),
        (Benefit.SHIPPING_FIXED_PRICE, _("Get shipping for a fixed price")),
    )
    benefit_type = forms.ChoiceField(
        choices=type_choices,
        label=_('Discount type'),
    )
    benefit_value = forms.DecimalField(
        label=_('Discount value'))

    def save(self, commit=True):
        instance = super(VoucherSetForm, self).save(commit)
        if commit:
            instance.generate_vouchers()
        return instance


class VoucherSetSearchForm(forms.Form):
    code = forms.CharField(required=False, label=_("Code"))
    is_active = forms.BooleanField(required=False, label=_("Is Active?"))

    def clean_code(self):
        return self.cleaned_data['code'].upper()
