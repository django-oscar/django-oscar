from django import forms

from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')


class MetaDataForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d'),
                                 label=_("Start date"), required=False)
    end_date = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d'),
                               label=_("End date"), required=False)

    class Meta:
        model = ConditionalOffer
        fields = ('name', 'description', 'start_date', 'end_date',
                  'max_basket_applications', 'max_user_applications',
                  'max_global_applications')


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


class PreviewForm(forms.Form):
    pass


class OfferSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Offer name"))
    is_active = forms.BooleanField(required=False, label=_("Is active?"))
