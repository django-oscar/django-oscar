from django import forms
from django.conf import settings
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from oscar.apps.promotions.conf import PROMOTION_CLASSES

from oscar.forms.fields import ExtendedURLField
from oscar.core.loading import get_classes

RawHTML, SingleProduct, PagePromotion, HandPickedProductList, OrderedProduct = get_classes('promotions.models',
    ['RawHTML', 'SingleProduct', 'PagePromotion', 'HandPickedProductList',
     'OrderedProduct'])


class PromotionTypeSelectForm(forms.Form):
    choices = []
    for klass in PROMOTION_CLASSES:
        choices.append((klass.classname(), klass._meta.verbose_name))
    promotion_type = forms.ChoiceField(choices=tuple(choices),
                                       label=_("Promotion type"))


class RawHTMLForm(forms.ModelForm):
    class Meta:
        model = RawHTML
        exclude = ('display_type',)


class HandPickedProductListForm(forms.ModelForm):
    class Meta:
        model = HandPickedProductList
        exclude = ('products',)


OrderedProductFormSet = inlineformset_factory(HandPickedProductList,
                                              OrderedProduct, extra=2)


class PagePromotionForm(forms.ModelForm):
    page_url = ExtendedURLField(label=_("URL"), verify_exists=True)
    position = forms.CharField(
        widget=forms.Select(choices=settings.OSCAR_PROMOTION_POSITIONS),
        label=_("Position"),
        help_text=_("Where in the page this content block will appear"))

    class Meta:
        model = PagePromotion
        exclude = ('display_order', 'clicks', 'content_type', 'object_id')

    def clean_page_url(self):
        page_url = self.cleaned_data.get('page_url')
        if not page_url:
            return page_url

        if page_url.startswith('http'):
            raise forms.ValidationError(
                _("Content blocks can only be linked to internal URLs"))

        if page_url.startswith('/') and not page_url.endswith('/'):
            page_url += '/'

        return page_url
