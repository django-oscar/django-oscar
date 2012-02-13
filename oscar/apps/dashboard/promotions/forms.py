from django import forms

from oscar.forms.fields import ExtendedURLField
from oscar.core.loading import get_classes
from oscar.apps.promotions.conf import PROMOTION_CLASSES

RawHTML, SingleProduct, PagePromotion = get_classes('promotions.models', 
    ['RawHTML', 'SingleProduct', 'PagePromotion'])


class PromotionTypeSelectForm(forms.Form):
    choices = []
    for klass in PROMOTION_CLASSES:
        choices.append((klass.classname(), klass._type))
    promotion_type = forms.ChoiceField(choices=tuple(choices))


class RawHTMLForm(forms.ModelForm):

    class Meta:
        model = RawHTML


POSITION_CHOICES = (('page', 'Page'),
                    ('right', 'Right-hand sidebar'),
                    ('left', 'Left-hand sidebar'))


class PagePromotionForm(forms.ModelForm):
    page_url = ExtendedURLField(label="URL")
    position = forms.CharField(widget=forms.Select(choices=POSITION_CHOICES),
                               help_text="""Where in the page this content
                                            block will appear""")

    class Meta:
        model = PagePromotion
        exclude = ('display_order', 'clicks', 'content_type', 'object_id')

    def clean_page_url(self):
        page_url = self.cleaned_data.get('page_url')
        if (page_url and page_url.startswith('/') and
            not page_url.endswith('/')):
            page_url += '/'
        return page_url

