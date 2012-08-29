from django import forms
from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _

User = get_model('user', 'User')
Notification = get_model('notification', 'notification')


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_("Email"))
    name = forms.CharField(required=False, label=_("Name"))


class NotificationUpdateForm(forms.ModelForm):
    class Meta:
        model = Notification
        exclude = ('confirm_key', 'unsubscribe_key')


class NotificationSearchForm(forms.Form):
    STATUS_CHOICES = (
        ('', '------------'),
    ) + Notification.STATUS_TYPES

    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)
    name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
