from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model
from oscar.forms import widgets

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')


def get_offer_type_choices():
    return (("", "---------"),) + tuple(choice for choice in ConditionalOffer.TYPE_CHOICES
                                        if choice[0] in [getattr(ConditionalOffer, const_name)
                                                         for const_name in settings.OSCAR_OFFERS_IMPLEMENTED_TYPES])


class MetaDataForm(forms.ModelForm):

    offer_type = forms.ChoiceField(label=_("Type"), choices=get_offer_type_choices)

    class Meta:
        model = ConditionalOffer
        fields = ('name', 'description', 'offer_type')

    def clean_offer_type(self):
        data = self.cleaned_data['offer_type']
        if (self.instance.pk is not None) and (self.instance.offer_type == ConditionalOffer.VOUCHER) and \
           ('offer_type' in self.changed_data) and self.instance.vouchers.exists():
            raise forms.ValidationError(_("This can only be changed if it has no vouchers attached to it"))
        return data


class RestrictionsForm(forms.ModelForm):

    start_datetime = forms.DateTimeField(
        widget=widgets.DateTimePickerInput(),
        label=_("Start date"), required=False)
    end_datetime = forms.DateTimeField(
        widget=widgets.DateTimePickerInput(),
        label=_("End date"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_datetime'].initial = timezone.now()

    class Meta:
        model = ConditionalOffer
        fields = ('start_datetime', 'end_datetime',
                  'max_basket_applications', 'max_user_applications',
                  'max_global_applications', 'max_discount',
                  'priority', 'exclusive', 'combinations')

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data['start_datetime']
        end = cleaned_data['end_datetime']
        if start and end and end < start:
            raise forms.ValidationError(_(
                "The end date must be after the start date"))
        exclusive = cleaned_data['exclusive']
        combinations = cleaned_data['combinations']
        if exclusive and combinations:
            raise forms.ValidationError(_('Exclusive offers cannot be combined'))
        return cleaned_data

    def save(self, *args, **kwargs):
        """Store the offer combinations.

        Also, and make sure the combinations are stored on the combine-able
        offers as well.
        """
        instance = super().save(*args, **kwargs)
        if instance.id:
            instance.combinations.clear()
            for offer in self.cleaned_data['combinations']:
                if offer != instance:
                    instance.combinations.add(offer)

            combined_offers = instance.combined_offers
            for offer in combined_offers:
                if offer == instance:
                    continue
                for otheroffer in combined_offers:
                    if offer == otheroffer:
                        continue
                    offer.combinations.add(otheroffer)
        return instance


class ConditionForm(forms.ModelForm):
    custom_condition = forms.ChoiceField(
        required=False,
        label=_("Custom condition"), choices=())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        custom_conditions = Condition.objects.all().exclude(
            proxy_class=None)
        if len(custom_conditions) > 0:
            # Initialise custom_condition field
            choices = [(c.id, str(c)) for c in custom_conditions]
            choices.insert(0, ('', ' --------- '))
            self.fields['custom_condition'].choices = choices
            condition = kwargs.get('instance')
            if condition:
                self.fields['custom_condition'].initial = condition.id
        else:
            # No custom conditions and so the type/range/value fields
            # are no longer optional
            for field in ('type', 'range', 'value'):
                self.fields[field].required = True

    class Meta:
        model = Condition
        fields = ['range', 'type', 'value']

    def clean(self):
        data = super().clean()

        # Check that either a condition has been entered or a custom condition
        # has been chosen
        if data.get('custom_condition'):
            if not data.get('range', None):
                raise forms.ValidationError(
                    _("A range is required"))
        elif not all([data.get('range'), data.get('type'), data.get('value')]):
            raise forms.ValidationError(
                _("Please either choose a range, type and value OR "
                  "select a custom condition"))

        return data

    def save(self, *args, **kwargs):
        # We don't save a new model if a custom condition has been chosen,
        # we simply return the instance that has been chosen
        if self.cleaned_data['custom_condition']:
            return Condition.objects.get(
                id=self.cleaned_data['custom_condition'])
        return super().save(*args, **kwargs)


class BenefitForm(forms.ModelForm):
    custom_benefit = forms.ChoiceField(
        required=False,
        label=_("Custom incentive"), choices=())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        custom_benefits = Benefit.objects.all().exclude(
            proxy_class=None)
        if len(custom_benefits) > 0:
            # Initialise custom_benefit field
            choices = [(c.id, str(c)) for c in custom_benefits]
            choices.insert(0, ('', ' --------- '))
            self.fields['custom_benefit'].choices = choices
            benefit = kwargs.get('instance')
            if benefit:
                self.fields['custom_benefit'].initial = benefit.id
        else:
            # No custom benefit and so the type fields
            # are no longer optional
            self.fields['type'].required = True

    class Meta:
        model = Benefit
        fields = ['range', 'type', 'value', 'max_affected_items']

    def clean(self):
        data = super().clean()

        # Check that either a benefit has been entered or a custom benfit
        # has been chosen
        if not any(data.values()):
            raise forms.ValidationError(
                _("Please either choose a range, type and value OR "
                  "select a custom incentive"))

        if data['custom_benefit']:
            if data.get('range') or data.get('type') or data.get('value'):
                raise forms.ValidationError(
                    _("No other options can be set if you are using a "
                      "custom incentive"))
        elif not data.get('type'):
            raise forms.ValidationError(
                _("Please either choose a range, type and value OR "
                  "select a custom incentive"))

        return data

    def save(self, *args, **kwargs):
        # We don't save a new model if a custom benefit has been chosen,
        # we simply return the instance that has been chosen
        if self.cleaned_data['custom_benefit']:
            return Benefit.objects.get(
                id=self.cleaned_data['custom_benefit'])
        return super().save(*args, **kwargs)


class OfferSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Offer name"))
    is_active = forms.NullBooleanField(required=False, label=_("Is active?"), widget=widgets.NullBooleanSelect)
    offer_type = forms.ChoiceField(required=False, label=_("Offer type"), choices=get_offer_type_choices)
    has_vouchers = forms.NullBooleanField(required=False, label=_("Has vouchers?"), widget=widgets.NullBooleanSelect)
    voucher_code = forms.CharField(required=False, label=_("Voucher code"))

    basic_fields = [
        'name',
        'is_active',
    ]

    @property
    def is_voucher_offer_type(self):
        return self.is_bound and (self.cleaned_data['offer_type'] == ConditionalOffer.VOUCHER)
