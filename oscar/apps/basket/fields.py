from django import forms
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.text import mark_safe

from oscar.forms.widgets import AdvancedChoice, AdvancedRadioSelect

class VariantChoice(AdvancedChoice):

    # Bootstrap 2 & 3 classes
    DISABLED_CLASSES = ['muted', 'text-muted']

    def __init__(self, label, disabled=False, href=None):
        self.href = href
        super(VariantChoice, self).__init__(label, disabled=disabled)

    def __unicode__(self):
        if self.href:
            if self.disabled:
                disabled = format_html(' class="{0}"', ' '.join(self.DISABLED_CLASSES))
            else:
                disabled = ''
            return force_text( format_html('<a href="{0}"{1}>{2}</a>', self.href, disabled, self.label) )
        else:
            return self.label

class VariantChoiceField(forms.ModelChoiceField):
    """
    Field that renders variant choices of the AddToBasket form.
    """

    def __init__(self, *args, **kwargs):
        if 'widget' not in kwargs:
            kwargs['widget'] = AdvancedRadioSelect()

        self.basket = kwargs.pop('basket')

        super(VariantChoiceField, self).__init__(*args, **kwargs)

    def label_from_instance(self, child):
        """
        Returns a custom label for each child choice.
        """
        attr_summary = child.attribute_summary
        if attr_summary:
            summary = attr_summary
        else:
            summary = child.get_title()

        # Check if it is available to buy
        info = self.basket.strategy.fetch_for_product(child)
        disabled = not info.availability.is_available_to_buy

        href = child.get_absolute_url()

        return VariantChoice(summary, disabled=disabled, href=href)