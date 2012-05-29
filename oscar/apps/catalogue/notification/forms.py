from django import forms


class NotificationForm(forms.Form):
    """
    """
    email = forms.EmailField(required=True, label=(u'Send notification to'))

    def __init__(self, *args, **kwargs):
        super(NotificationForm, self).__init__(*args, **kwargs)
        user = self.initial.get('user', None)
        if user and user.is_authenticated():
            self.fields['email'].widget = forms.HiddenInput()

            if not self.initial.get('email', None):
                self.initial['email'] = user.email
