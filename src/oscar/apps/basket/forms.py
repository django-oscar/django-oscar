from django import forms
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.db.models import Sum
from django.forms.utils import ErrorDict
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model
from oscar.forms import widgets

Line = get_model('basket', 'line')
Basket = get_model('basket', 'basket')
Option = get_model('catalogue', 'option')
Product = get_model('catalogue', 'product')


def _option_text_field(form, product, option):
    return forms.CharField(label=option.name, required=option.required, help_text=option.help_text)


def _option_integer_field(form, product, option):
    return forms.IntegerField(label=option.name, required=option.required, help_text=option.help_text)


def _option_boolean_field(form, product, option):
    return forms.BooleanField(label=option.name, required=option.required, help_text=option.help_text)


def _option_float_field(form, product, option):
    return forms.FloatField(label=option.name, required=option.required, help_text=option.help_text)


def _option_date_field(form, product, option):
    return forms.DateField(
        label=option.name,
        required=option.required,
        widget=forms.widgets.SelectDateWidget,
        help_text=option.help_text
    )


def _option_select_field(form, product, option):
    return forms.ChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        help_text=option.help_text
    )


def _option_radio_field(form, product, option):
    return forms.ChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        widget=forms.RadioSelect,
        help_text=option.help_text
    )


def _option_multi_select_field(form, product, option):
    return forms.MultipleChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        help_text=option.help_text
    )


def _option_checkbox_field(form, product, option):
    return forms.MultipleChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        widget=forms.CheckboxSelectMultiple,
        help_text=option.help_text
    )


class BasketLineForm(forms.ModelForm):
    quantity = forms.IntegerField(label=_('Quantity'), min_value=0, required=False, initial=1)
    save_for_later = forms.BooleanField(
        initial=False, required=False, label=_('Save for Later'))

    def __init__(self, strategy, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.strategy = strategy

        # Evaluate max allowed quantity check only if line still exists, in
        # order to avoid check run against missing instance -
        # https://github.com/django-oscar/django-oscar/issues/2873.
        if self.instance.id:
            max_allowed_quantity = None
            num_available = getattr(self.instance.purchase_info.availability, 'num_available', None)
            basket_max_allowed_quantity = self.instance.basket.max_allowed_quantity()[0]
            if all([num_available, basket_max_allowed_quantity]):
                max_allowed_quantity = min(num_available, basket_max_allowed_quantity)
            else:
                max_allowed_quantity = num_available or basket_max_allowed_quantity
            if max_allowed_quantity:
                self.fields['quantity'].widget.attrs['max'] = max_allowed_quantity

    def full_clean(self):
        if not self.instance.id:
            self.cleaned_data = {}
            self._errors = ErrorDict()
            return
        return super().full_clean()

    def has_changed(self):
        if not self.instance.id:
            return False
        return super().has_changed()

    def clean_quantity(self):
        qty = self.cleaned_data['quantity'] or 0
        if qty > 0:
            self.check_max_allowed_quantity(qty)
            self.check_permission(qty)
        return qty

    def check_max_allowed_quantity(self, qty):
        # Since `Basket.is_quantity_allowed` checks quantity of added product
        # against total number of the products in the basket, instead of sending
        # updated quantity of the product, we send difference between current
        # number and updated. Thus, product already in the basket and we don't
        # add second time, just updating number of items.
        qty_delta = qty - self.instance.quantity
        is_allowed, reason = self.instance.basket.is_quantity_allowed(qty_delta)
        if not is_allowed:
            raise forms.ValidationError(reason)

    def check_permission(self, qty):
        policy = self.instance.purchase_info.availability
        is_available, reason = policy.is_purchase_permitted(
            quantity=qty)
        if not is_available:
            raise forms.ValidationError(reason)

    class Meta:
        model = Line
        fields = ['quantity']


class SavedLineForm(forms.ModelForm):
    move_to_basket = forms.BooleanField(initial=False, required=False,
                                        label=_('Move to Basket'))

    class Meta:
        model = Line
        fields = ('id', 'move_to_basket')

    def __init__(self, strategy, basket, *args, **kwargs):
        self.strategy = strategy
        self.basket = basket
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['move_to_basket']:
            # skip further validation (see issue #666)
            return cleaned_data

        # Get total quantity of all lines with this product (there's normally
        # only one but there can be more if you allow product options).
        lines = self.basket.lines.filter(product=self.instance.product)
        current_qty = lines.aggregate(Sum('quantity'))['quantity__sum'] or 0
        desired_qty = current_qty + self.instance.quantity

        result = self.strategy.fetch_for_product(self.instance.product)
        is_available, reason = result.availability.is_purchase_permitted(
            quantity=desired_qty)
        if not is_available:
            raise forms.ValidationError(reason)
        return cleaned_data


class BasketVoucherForm(forms.Form):
    code = forms.CharField(max_length=128, label=_('Code'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()


class AddToBasketForm(forms.Form):

    OPTION_FIELD_FACTORIES = {
        Option.TEXT: _option_text_field,
        Option.INTEGER: _option_integer_field,
        Option.BOOLEAN: _option_boolean_field,
        Option.FLOAT: _option_float_field,
        Option.DATE: _option_date_field,
        Option.SELECT: _option_select_field,
        Option.RADIO: _option_radio_field,
        Option.MULTI_SELECT: _option_multi_select_field,
        Option.CHECKBOX: _option_checkbox_field,
    }

    quantity = forms.IntegerField(initial=1, min_value=1, label=_('Quantity'))

    def __init__(self, basket, product, *args, **kwargs):
        # Note, the product passed in here isn't necessarily the product being
        # added to the basket. For child products, it is the *parent* product
        # that gets passed to the form. An optional product_id param is passed
        # to indicate the ID of the child product being added to the basket.
        self.basket = basket
        self.parent_product = product

        super().__init__(*args, **kwargs)

        # Dynamically build fields
        if product.is_parent:
            self._create_parent_product_fields(product)
        self._create_product_fields(product)

    # Dynamic form building methods

    def _create_parent_product_fields(self, product):
        """
        Adds the fields for a "group"-type product (eg, a parent product with a
        list of children.

        Currently requires that a stock record exists for the children
        """
        choices = []
        disabled_values = []
        for child in product.children.public():
            # Build a description of the child, including any pertinent
            # attributes
            attr_summary = child.attribute_summary
            if attr_summary:
                summary = attr_summary
            else:
                summary = child.get_title()

            # Check if it is available to buy
            info = self.basket.strategy.fetch_for_product(child)
            if not info.availability.is_available_to_buy:
                disabled_values.append(child.id)

            choices.append((child.id, summary))

        self.fields['child_id'] = forms.ChoiceField(
            choices=tuple(choices), label=_("Variant"),
            widget=widgets.AdvancedSelect(disabled_values=disabled_values))

    def _create_product_fields(self, product):
        """
        Add the product option fields.
        """
        for option in product.options:
            self._add_option_field(product, option)

    def _add_option_field(self, product, option):
        """
        Creates the appropriate form field for the product option.

        This is designed to be overridden so that specific widgets can be used
        for certain types of options.
        """
        option_field = self.OPTION_FIELD_FACTORIES.get(option.type, _option_text_field)(self, product, option)
        self.fields[option.code] = option_field

    # Cleaning

    def clean_child_id(self):
        try:
            child = self.parent_product.children.get(
                id=self.cleaned_data['child_id'])
        except Product.DoesNotExist:
            raise forms.ValidationError(
                _("Please select a valid product"))

        # To avoid duplicate SQL queries, we cache a copy of the loaded child
        # product as we're going to need it later.
        self.child_product = child

        return self.cleaned_data['child_id']

    def clean_quantity(self):
        # Check that the proposed new line quantity is sensible
        qty = self.cleaned_data['quantity']
        basket_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.basket.num_items
            max_allowed = basket_threshold - total_basket_quantity
            if qty > max_allowed:
                raise forms.ValidationError(
                    _("Due to technical limitations we are not able to ship"
                      " more than %(threshold)d items in one order. Your"
                      " basket currently has %(basket)d items.")
                    % {'threshold': basket_threshold,
                       'basket': total_basket_quantity})
        return qty

    @property
    def product(self):
        """
        The actual product being added to the basket
        """
        # Note, the child product attribute is saved in the clean_child_id
        # method
        return getattr(self, 'child_product', self.parent_product)

    def clean(self):
        info = self.basket.strategy.fetch_for_product(self.product)

        # Check that a price was found by the strategy
        if not info.price.exists:
            raise forms.ValidationError(
                _("This product cannot be added to the basket because a "
                  "price could not be determined for it."))

        # Check currencies are sensible
        if (self.basket.currency
                and info.price.currency != self.basket.currency):
            raise forms.ValidationError(
                _("This product cannot be added to the basket as its currency "
                  "isn't the same as other products in your basket"))

        # Check user has permission to add the desired quantity to their
        # basket.
        current_qty = self.basket.product_quantity(self.product)
        desired_qty = current_qty + self.cleaned_data.get('quantity', 1)
        is_permitted, reason = info.availability.is_purchase_permitted(
            desired_qty)
        if not is_permitted:
            raise forms.ValidationError(reason)

        return self.cleaned_data

    # Helpers

    def cleaned_options(self):
        """
        Return submitted options in a clean format
        """
        options = []
        for option in self.parent_product.options:
            if option.code in self.cleaned_data:
                value = self.cleaned_data[option.code]
                if option.required or value not in EMPTY_VALUES:
                    options.append(
                        {"option": option, "value": value}
                    )
        return options


class SimpleAddToBasketMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'quantity' in self.fields:
            self.fields['quantity'].initial = 1
            self.fields['quantity'].widget = forms.HiddenInput()


class SimpleAddToBasketForm(SimpleAddToBasketMixin, AddToBasketForm):
    """
    Simplified version of the add to basket form where the quantity is
    defaulted to 1 and rendered in a hidden widget

    If you changed `AddToBasketForm`, you'll need to override this class
    as well by doing:

    class SimpleAddToBasketForm(SimpleAddToBasketMixin, AddToBasketForm):
        pass
    """
