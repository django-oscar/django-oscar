from django import forms

from oscar.core.loading import get_classes

RawHTML, SingleProduct = get_classes('promotions.models', 
    ['RawHTML', 'SingleProduct'])


class PromotionTypeSelectForm(forms.Form):
    promotion_type = forms.ChoiceField(choices=(('singleproduct', u'Single product'),
                                                ('rawhtml', u'Raw HTML')))


class RawHTMLForm(forms.ModelForm):

    class Meta:
        model = RawHTML

