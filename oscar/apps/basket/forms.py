from django import forms
from django.db.models import get_model

basketline_model = get_model('basket', 'line')
basket_model = get_model('basket', 'basket')

class BasketLineForm(forms.ModelForm):
    save_for_later = forms.BooleanField(initial=False,required=False)
    
    class Meta:
        model = basketline_model
        exclude = ('basket', 'product', 'line_reference', )


class FormFactory(object):
    u"""Factory for creating the "add-to-basket" forms."""
    
    def create(self, item, values=None):
        u"""For dynamically creating add-to-basket forms for a given product"""
        self.fields = {'action': forms.CharField(widget=forms.HiddenInput(), initial='add'),
                       'product_id': forms.IntegerField(widget=forms.HiddenInput(), min_value=1),
                       'quantity': forms.IntegerField(min_value=1)}
        self.values = values
        if not self.values:
            self.values = {'action': 'add', 
                           'product_id': item.id, 
                           'quantity': 1}
        if item.is_group:
            self._create_group_product_fields(item)
        else:
            self._create_product_fields(item)

        # See http://www.b-list.org/weblog/2008/nov/09/dynamic-forms/ for 
        # advice on how this works.
        form_class = type('AddToBasketForm', (forms.BaseForm,), {'base_fields': self.fields})
        
        return form_class(self.values)

    def _create_group_product_fields(self, item):
        u"""
        Adds the fields for a "group"-type product (eg, a parent product with a
        list of variants.
        """
        choices = []
        for variant in item.variants.all():
            if variant.has_stockrecord:
                summary = u"%s (%s) - %.2f" % (variant.get_title(), variant.attribute_summary(), 
                                               variant.stockrecord.price_incl_tax)
                choices.append((variant.id, summary))
        self.fields['product_id'] = forms.ChoiceField(choices=tuple(choices))
    
    def _create_product_fields(self, item):
        u"""Add the product option fields."""
        for option in item.options:
            self._add_option_field(item, option)
    
    def _add_option_field(self, item, option):
        u"""
        Creates the appropriate form field for the product option.
        
        This is designed to be overridden so that specific widgets can be used for 
        certain types of options.
        """
        self.fields[option.code] = forms.CharField()
    

    
