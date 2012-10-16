from django import forms
from django.db.models import get_model
from django.template import Template, TemplateSyntaxError
from django.utils.translation import ugettext_lazy as _

from oscar.forms import widgets

CommunicationEventType = get_model('customer', 'CommunicationEventType')


class CommunicationEventTypeForm(forms.ModelForm):
    email_subject_template = forms.CharField(
        label=_("Email subject template"))
    email_body_template = forms.CharField(
        label=_("Email body text template"), required=True,
        widget=forms.widgets.Textarea(attrs={'class': 'plain'}))
    email_body_html_template = forms.CharField(
        label=_("Email body HTML template"), required=True,
        widget=widgets.WYSIWYGTextArea)
    preview_email = forms.EmailField(label=_("Preview email"),
                                     required=False)

    def validate_template(self, value):
        try:
            Template(value)
        except TemplateSyntaxError, e:
            raise forms.ValidationError(e.message)

    def clean_email_subject_template(self):
        subject = self.cleaned_data['email_subject_template']
        self.validate_template(subject)
        return subject

    def clean_email_body_template(self):
        body = self.cleaned_data['email_body_template']
        self.validate_template(body)
        return body

    def clean_email_body_html_template(self):
        body = self.cleaned_data['email_body_html_template']
        self.validate_template(body)
        return body

    class Meta:
        model = CommunicationEventType
        exclude = ('code', 'category', 'sms_template')
