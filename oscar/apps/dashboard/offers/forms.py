import datetime

from django import forms

from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')


class MetaDataForm(forms.ModelForm):
    class Meta:
        model = ConditionalOffer
        fields = ('name', 'description')


class RestrictionsForm(forms.ModelForm):
    format = '%Y-%m-%d %H:%M'
    start_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(format=format),
        label=_("Start date"), required=False)
    end_datetime = forms.DateTimeField(widget=forms.DateTimeInput(format=format),
                               label=_("End date"), required=False)

    def __init__(self, *args, **kwargs):
        super(RestrictionsForm, self).__init__(*args, **kwargs)
        today = datetime.date.today()
        self.fields['start_datetime'].initial = today.strftime(self.format)

    class Meta:
        model = ConditionalOffer
        fields = ('start_datetime', 'end_datetime',
                  'max_basket_applications', 'max_user_applications',
                  'max_global_applications', 'max_discount')

    def clean(self):
        cleaned_data = super(RestrictionsForm, self).clean()
        start = cleaned_data['start_datetime']
        end = cleaned_data['end_datetime']
        if start and end and end < start:
            raise forms.ValidationError(_(
                "The end date must be after the start date"))
        return cleaned_data


class ConditionForm(forms.ModelForm):
    custom_condition = forms.ChoiceField(
        required=False,
        label=_("Custom condition"), choices=())

    def __init__(self, *args, **kwargs):
        super(ConditionForm, self).__init__(*args, **kwargs)

        custom_conditions = Condition.objects.all().exclude(
            proxy_class=None)
        if len(custom_conditions) > 0:
            # Initialise custom_condition field
            choices = [(c.id, c.__unicode__()) for c in custom_conditions]
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
        exclude = ('proxy_class',)

    def clean(self):
        data = super(ConditionForm, self).clean()

        # Check that either a condition has been entered or a custom condition
        # has been chosen
        if not any(data.values()):
            raise forms.ValidationError(
                _("Please either choose a range, type and value OR "
                  "select a custom condition"))

        if not data['custom_condition']:
            if not data['range']:
                raise

        return data

    def save(self, *args, **kwargs):
        # We don't save a new model if a custom condition has been chosen,
        # we simply return the instance that has been chosen
        if self.cleaned_data['custom_condition']:
            return Condition.objects.get(
                id=self.cleaned_data['custom_condition'])
        return super(ConditionForm, self).save(*args, **kwargs)


class BenefitForm(forms.ModelForm):

    class Meta:
        model = Benefit


class OfferSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Offer name"))
    is_active = forms.BooleanField(required=False, label=_("Is active?"))
