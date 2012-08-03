from django import forms
from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _

User = get_model('user', 'User')
ProductNotification = get_model('notification', 'productnotification')


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_("Email"))
    name = forms.CharField(required=False, label=_("Name"))


class ProductNotificationUpdateForm(forms.ModelForm):
    class Meta:
        model = ProductNotification
        exclude = ('confirm_key', 'unsubscribe_key')


class ProductNotificationSearchForm(forms.Form):
    STATUS_CHOICES = (
        ('', '------------'),
    ) + ProductNotification.STATUS_TYPES

    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)
    name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
