from django import forms

from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')


class MetaDataForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d'),
                                 label=_("Start date"))
    end_date = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d'),
                               label=_("End date"))

    class Meta:
        model = ConditionalOffer
        fields = ('name', 'description', 'start_date', 'end_date',)


class ConditionForm(forms.ModelForm):

    class Meta:
        model = Condition


class BenefitForm(forms.ModelForm):

    class Meta:
        model = Benefit


class PreviewForm(forms.Form):
    pass


class OfferSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Offer name"))
    is_active = forms.BooleanField(required=False, label=_("Is active?"))
