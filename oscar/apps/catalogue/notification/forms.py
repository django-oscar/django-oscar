from django import forms
from django.utils.translation import ugettext_lazy as _


class ProductNotificationForm(forms.Form):
    """
    Form providing a single email field for signing up to a notification. If
    ``email`` or ``user`` are provided as initial values these values are
    used to update the ``email`` field. If ``user`` is specified and the
    user is registered and logged in, the ``email`` field is hidden in the
    HTML template.
    """
    email = forms.EmailField(required=True, label=_(u'Send notification to'),
                             widget=forms.TextInput(attrs={
                                 'placeholder': _('Enter Your Email')
                             }))

    def __init__(self, *args, **kwargs):
        super(ProductNotificationForm, self).__init__(*args, **kwargs)
        user = self.initial.get('user', None)
        if user and user.is_authenticated():
            self.fields['email'].widget = forms.HiddenInput()

            if not self.initial.get('email', None):
                self.initial['email'] = user.email
