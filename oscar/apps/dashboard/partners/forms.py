from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model
from django import forms


Partner = get_model('partner', 'Partner')


class PartnerSearchForm(forms.Form):
    name = forms.CharField(required=False, label=_("Partner name"))


class PartnerCreateForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ('name',)
