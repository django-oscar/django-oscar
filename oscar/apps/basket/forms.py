from django import forms
from django.conf import settings
from django.db.models import get_model
from django.utils.translation import gettext_lazy as _

basketline_model = get_model('basket', 'line')
basket_model = get_model('basket', 'basket')
Product = get_model('catalogue', 'product')


class BasketLineForm(forms.ModelForm):
    save_for_later = forms.BooleanField(initial=False, required=False)

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        basket_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.instance.basket.num_items
            max_allowed = basket_threshold - total_basket_quantity
            if qty > max_allowed:
                raise forms.ValidationError(
                    _("Due to technical limitations we are not able to ship"
                      " more than %(threshold)d items in one order. Your basket"
                      " currently has %(basket)d items.") % {
                            'threshold': basket_threshold,
                            'basket': total_basket_quantity,
                    })
        return qty

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


class ProductSelectionForm(forms.Form):
    product_id = forms.IntegerField(min_value=1)

    def clean_product_id(self):
        id = self.cleaned_data['product_id']

        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            raise forms.ValidationError(_("This product is not available for purchase"))


class AddToBasketForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput(), min_value=1)
    quantity = forms.IntegerField(initial=1, min_value=1)

    def __init__(self, basket, instance, *args, **kwargs):
        super(AddToBasketForm, self).__init__(*args, **kwargs)
        self.basket = basket
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
            raise forms.ValidationError(_("This product is not available for purchase"))
        return id

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        basket_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.basket.num_items
            max_allowed = basket_threshold - total_basket_quantity
            if qty > max_allowed:
                raise forms.ValidationError(
                    _("Due to technical limitations we are not able to ship"
                      " more than %(threshold)d items in one order. Your basket"
                      " currently has %(basket)d items.") % {
                            'threshold': basket_threshold,
                            'basket': total_basket_quantity,
                    })
        return qty

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


