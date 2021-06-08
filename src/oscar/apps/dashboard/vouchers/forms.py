from django import forms
from django.db import transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from oscar.apps.voucher.utils import get_unused_code
from oscar.core.loading import get_model
from oscar.forms import widgets

Voucher = get_model('voucher', 'Voucher')
VoucherSet = get_model('voucher', 'VoucherSet')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


class VoucherForm(forms.ModelForm):
    """
    A specialised form for creating a voucher model, and capturing the offers
    that apply to it.
    """
    offers = forms.ModelMultipleChoiceField(
        label=_("Which offers apply for this voucher?"),
        queryset=ConditionalOffer.objects.filter(offer_type=ConditionalOffer.VOUCHER),
    )

    class Meta:
        model = Voucher
        fields = [
            'name',
            'code',
            'start_datetime',
            'end_datetime',
            'usage',
        ]
        widgets = {
            'start_datetime': widgets.DateTimePickerInput(),
            'end_datetime': widgets.DateTimePickerInput(),
        }

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()


class VoucherSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Name"))
    code = forms.CharField(required=False, label=_("Code"))
    offer_name = forms.CharField(required=False, label=_("Offer name"))
    is_active = forms.NullBooleanField(required=False, label=_("Is active?"), widget=widgets.NullBooleanSelect)
    in_set = forms.NullBooleanField(required=False, label=_("In voucher set?"), widget=widgets.NullBooleanSelect)
    has_offers = forms.NullBooleanField(required=False, label=_("Has offers?"), widget=widgets.NullBooleanSelect)

    basic_fields = [
        'name',
        'code',
        'is_active',
        'in_set',
    ]

    def clean_code(self):
        return self.cleaned_data['code'].upper()


class VoucherSetForm(forms.ModelForm):
    usage = forms.ChoiceField(choices=(("", "---------"),) + Voucher.USAGE_CHOICES, label=_("Usage"))

    offers = forms.ModelMultipleChoiceField(
        label=_("Which offers apply for this voucher set?"),
        queryset=ConditionalOffer.objects.filter(offer_type=ConditionalOffer.VOUCHER),
    )

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

    def clean_count(self):
        data = self.cleaned_data['count']
        if (self.instance.pk is not None) and (data < self.instance.count):
            detail_url = reverse('dashboard:voucher-set-detail', kwargs={'pk': self.instance.pk})
            raise forms.ValidationError(mark_safe(
                _('This cannot be used to delete vouchers (currently %s) in this set. '
                  'You can do that on the <a href="%s">detail</a> page.') % (self.instance.count, detail_url)))
        return data

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            usage = self.cleaned_data['usage']
            offers = self.cleaned_data['offers']
            if instance is not None:
                # Update vouchers in this set
                for i, voucher in enumerate(instance.vouchers.order_by('date_created')):
                    voucher.name = "%s - %d" % (instance.name, i + 1)
                    voucher.usage = usage
                    voucher.start_datetime = instance.start_datetime
                    voucher.end_datetime = instance.end_datetime
                    voucher.save()
                    voucher.offers.set(offers)
            # Add vouchers to this set
            vouchers_added = False
            for i in range(instance.vouchers.count(), instance.count):
                voucher = Voucher.objects.create(name="%s - %d" % (instance.name, i + 1),
                                                 code=get_unused_code(length=instance.code_length),
                                                 voucher_set=instance,
                                                 usage=usage,
                                                 start_datetime=instance.start_datetime,
                                                 end_datetime=instance.end_datetime)
                voucher.offers.add(*offers)
                vouchers_added = True
            if vouchers_added:
                instance.update_count()
        return instance


class VoucherSetSearchForm(forms.Form):
    code = forms.CharField(required=False, label=_("Code"))

    def clean_code(self):
        return self.cleaned_data['code'].upper()
