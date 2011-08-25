from django import forms
from django.db.models import get_model

basketline_model = get_model('basket', 'line')
basket_model = get_model('basket', 'basket')
Product = get_model('catalogue', 'product')


class BasketLineForm(forms.ModelForm):
    save_for_later = forms.BooleanField(initial=False, required=False)
    
    class Meta:
        model = basketline_model
        exclude = ('basket', 'product', 'line_reference', )


class SavedLineForm(forms.ModelForm):
    move_to_basket = forms.BooleanField(initial=False, required=False)
    
    class Meta:
        model = basketline_model
        exclude = ('basket', 'product', 'line_reference', 'quantity', )


class BasketVoucherForm(forms.Form):
    code = forms.CharField(max_length=128)
    
    def __init__(self, *args, **kwargs):
        return super(BasketVoucherForm, self).__init__(*args,**kwargs)


class AddToBasketForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput(), min_value=1)
    quantity = forms.IntegerField(initial=1, min_value=1)
    
    def __init__(self, instance, *args, **kwargs):
        super(AddToBasketForm, self).__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            if instance.is_group:
                self._create_group_product_fields(instance)
            else:
                self._create_product_fields(instance)
    
    def clean_product_id(self):
        id = self.cleaned_data['product_id']
        product = Product.objects.get(id=id)
        if not product.has_stockrecord or not product.stockrecord.is_available_to_buy:
            raise forms.ValidationError("This product is not available for purchase")
        return id

    def _create_group_product_fields(self, item):
        """
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
    

