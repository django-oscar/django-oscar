from django import forms
from django.utils.translation import ugettext_lazy as _
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

Category = get_model('catalogue', 'Category')

CategoryForm = movenodeform_factory(
    Category,
    fields=['name', 'description', 'image'])


class StockAlertSearchForm(forms.Form):
    status = forms.CharField(label=_('Status'))