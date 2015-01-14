from django import forms

from oscar.forms.widgets import AdvancedSelect

class VariantChoice(object):
    """
    Represents a simplified choice for a variant.
    Includes a 'summary' which is the label, as well as a
    'disabled' attribute which tells the underlying widget
    to disable this choice.
    """

    def __init__(self, summary, disabled):
        self.summary = summary
        self.disabled = disabled

    def __str__(self):
        return self.summary

class VariantChoiceField(forms.ModelChoiceField):
    """
    Field that renders variant choices of the AddToBasket form.
    """

    def __init__(self, *args, **kwargs):
        if 'widget' not in kwargs:
            kwargs['widget'] = AdvancedSelect()

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

        return VariantChoice(summary, disabled)