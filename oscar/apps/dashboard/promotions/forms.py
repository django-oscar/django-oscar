from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from oscar.forms.fields import ExtendedURLField
from oscar.core.loading import get_classes
from oscar.apps.promotions.conf import PROMOTION_CLASSES, PROMOTION_POSITIONS

RawHTML, SingleProduct, PagePromotion, HandPickedProductList, OrderedProduct = get_classes('promotions.models', 
    ['RawHTML', 'SingleProduct', 'PagePromotion', 'HandPickedProductList',
     'OrderedProduct'])


class PromotionTypeSelectForm(forms.Form):
    choices = []
    for klass in PROMOTION_CLASSES:
        choices.append((klass.classname(), klass._type))
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
    page_url = ExtendedURLField(label=_("URL"))
    position = forms.CharField(widget=forms.Select(choices=PROMOTION_POSITIONS),
                               label=_("Position"),
                               help_text=_("Where in the page this content block will appear"))

    class Meta:
        model = PagePromotion
        exclude = ('display_order', 'clicks', 'content_type', 'object_id')

    def clean_page_url(self):
        page_url = self.cleaned_data.get('page_url')
        if (page_url and page_url.startswith('/') and
            not page_url.endswith('/')):
            page_url += '/'
        return page_url

