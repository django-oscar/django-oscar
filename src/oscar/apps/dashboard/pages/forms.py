from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.core.loading import get_model
from oscar.core.validators import URLDoesNotExistValidator

FlatPage = get_model('flatpages', 'FlatPage')


class PageSearchForm(forms.Form):
    """
    Search form to filter pages by *title.
    """
    title = forms.CharField(
        required=False, label=pgettext_lazy(u"Page title", u"Title"))


class PageUpdateForm(forms.ModelForm):
    """
    Update form to create/update flatpages. It provides a *title*, *url*,
    and *content* field. The specified URL will be validated and check if
    the same URL already exists in the system.
    """
    url = forms.CharField(max_length=128, required=False, label=_("URL"),
                          help_text=_("Example: '/about/contact/'."))

    def clean_url(self):
        """
        Validate the input for field *url* checking if the specified
        URL already exists. If it is an actual update and the URL has
        not been changed, validation will be skipped.

        Returns cleaned URL or raises an exception.
        """
        url = self.cleaned_data['url']
        if 'url' in self.changed_data:
            if not url.endswith('/'):
                url += '/'
            URLDoesNotExistValidator()(url)
        return url

    class Meta:
        model = FlatPage
        fields = ('title', 'url', 'content')
