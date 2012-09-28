from django import forms
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

CommunicationEventType = get_model('customer', 'CommunicationEventType')


class CommunicationEventTypeForm(forms.ModelForm):
    preview_email = forms.EmailField(label=_("Preview email"),
                                     required=False)

    class Meta:
        model = CommunicationEventType
        exclude = ('code', 'category', 'sms_template')
