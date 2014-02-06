from django import forms
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_model
from oscar.core.compat import get_user_model

User = get_user_model()
ProductAlert = get_model('customer', 'ProductAlert')


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_("Email"))
    name = forms.CharField(required=False, label=_("Name"))


class ProductAlertUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProductAlertUpdateForm, self).__init__(*args, **kwargs)
        alert = kwargs['instance']
        if alert.user:
            # Remove 'unconfirmed' from list of available choices when editing
            # an alert for a real user
            choices = self.fields['status'].choices
            del choices[0]
            self.fields['status'].choices = choices

    class Meta:
        model = ProductAlert
        exclude = ('product', 'user', 'email', 'key',
                   'date_confirmed', 'date_cancelled', 'date_closed')


class ProductAlertSearchForm(forms.Form):
    STATUS_CHOICES = (
        ('', '------------'),
    ) + ProductAlert.STATUS_CHOICES

    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES,
                               label=_('Status'))
    name = forms.CharField(required=False, label=_('Name'))
    email = forms.EmailField(required=False, label=_('Email'))
