from django import forms
from django.db.models import get_model
from django.template import Template, TemplateSyntaxError
from django.utils.translation import ugettext_lazy as _

CommunicationEventType = get_model('customer', 'CommunicationEventType')


class CommunicationEventTypeForm(forms.ModelForm):
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
