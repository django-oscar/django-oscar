from django import forms
from django.core import exceptions
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_class, get_model
from oscar.core.utils import slugify
from oscar.forms.widgets import ImageInput

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'StockRecord')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductImage = get_model('catalogue', 'ProductImage')
ProductRecommendation = get_model('catalogue', 'ProductRecommendation')
ProductSelect = get_class('dashboard.catalogue.widgets', 'ProductSelect')

CategoryForm = movenodeform_factory(
    Category,
    fields=['name', 'description', 'image'])


class ProductClassSelectForm(forms.Form):
    """
    Form which is used before creating a product to select it's product class
    """

    product_class = forms.ModelChoiceField(
        label=_("Create a new product of type"),
        empty_label=_("-- Choose type --"),
        queryset=ProductClass.objects.all())

    def __init__(self, *args, **kwargs):
        """
        If there's only one product class, pre-select it
        """
        super(ProductClassSelectForm, self).__init__(*args, **kwargs)
        qs = self.fields['product_class'].queryset
        if not kwargs.get('initial') and len(qs) == 1:
            self.fields['product_class'].initial = qs[0]


class ProductSearchForm(forms.Form):
    upc = forms.CharField(max_length=16, required=False, label=_('UPC'))
    title = forms.CharField(
        max_length=255, required=False, label=_('Product title'))

    def clean(self):
        cleaned_data = super(ProductSearchForm, self).clean()
        cleaned_data['upc'] = cleaned_data['upc'].strip()
        cleaned_data['title'] = cleaned_data['title'].strip()
        return cleaned_data


class StockRecordForm(forms.ModelForm):

    def __init__(self, product_class, user, *args, **kwargs):
        # The user kwarg is not used by stock StockRecordForm. We pass it
        # anyway in case one wishes to customise the partner queryset
        self.user = user
        super(StockRecordForm, self).__init__(*args, **kwargs)

        # Restrict accessible partners for non-staff users
        if not self.user.is_staff:
            self.fields['partner'].queryset = self.user.partners.all()

        # If not tracking stock, we hide the fields
        if not product_class.track_stock:
            for field_name in ['num_in_stock', 'low_stock_treshold']:
                if field_name in self.fields:
                    del self.fields[field_name]
        else:
            for field_name in ['price_excl_tax', 'num_in_stock']:
                if field_name in self.fields:
                    self.fields[field_name].required = True

    class Meta:
        model = StockRecord
        fields = [
            'partner', 'partner_sku',
            'price_currency', 'price_excl_tax', 'price_retail', 'cost_price',
            'num_in_stock', 'low_stock_threshold',
        ]


BaseStockRecordFormSet = inlineformset_factory(
    Product, StockRecord, form=StockRecordForm, extra=1)


class StockRecordFormSet(BaseStockRecordFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        self.user = user
        self.require_user_stockrecord = not user.is_staff
        self.product_class = product_class

        if not user.is_staff and \
           'instance' in kwargs and \
           'queryset' not in kwargs:
            kwargs.update({
                'queryset': StockRecord.objects.filter(product=kwargs['instance'],
                                                       partner__in=user.partners.all())
            })

        super(StockRecordFormSet, self).__init__(*args, **kwargs)
        self.set_initial_data()

    def set_initial_data(self):
        """
        If user has only one partner associated, set the first
        stock record's partner to it. Can't pre-select for staff users as
        they're allowed to save a product without a stock record.

        This is intentionally done after calling __init__ as passing initial
        data to __init__ creates a form for each list item. So depending on
        whether we can pre-select the partner or not, we'd end up with 1 or 2
        forms for an unbound form.
        """
        if self.require_user_stockrecord:
            try:
                user_partner = self.user.partners.get()
            except (exceptions.ObjectDoesNotExist,
                    exceptions.MultipleObjectsReturned):
                pass
            else:
                partner_field = self.forms[0].fields.get('partner', None)
                if partner_field and partner_field.initial is None:
                    partner_field.initial = user_partner

    def _construct_form(self, i, **kwargs):
        kwargs['product_class'] = self.product_class
        kwargs['user'] = self.user
        return super(StockRecordFormSet, self)._construct_form(
            i, **kwargs)

    def clean(self):
        """
        If the user isn't a staff user, this validation ensures that at least
        one stock record's partner is associated with a users partners.
        """
        if any(self.errors):
            return
        if self.require_user_stockrecord:
            stockrecord_partners = set([form.cleaned_data.get('partner', None)
                                        for form in self.forms])
            user_partners = set(self.user.partners.all())
            if not user_partners & stockrecord_partners:
                raise exceptions.ValidationError(
                    _("At least one stock record must be set to a partner that"
                      " you're associated with."))


def _attr_text_field(attribute):
    return forms.CharField(label=attribute.name,
                           required=attribute.required)


def _attr_textarea_field(attribute):
    return forms.CharField(label=attribute.name,
                           widget=forms.Textarea(),
                           required=attribute.required)


def _attr_integer_field(attribute):
    return forms.IntegerField(label=attribute.name,
                              required=attribute.required)


def _attr_boolean_field(attribute):
    return forms.BooleanField(label=attribute.name,
                              required=attribute.required)


def _attr_float_field(attribute):
    return forms.FloatField(label=attribute.name,
                            required=attribute.required)


def _attr_date_field(attribute):
    return forms.DateField(label=attribute.name,
                           required=attribute.required,
                           widget=forms.widgets.DateInput)


def _attr_option_field(attribute):
    return forms.ModelChoiceField(
        label=attribute.name,
        required=attribute.required,
        queryset=attribute.option_group.options.all())


def _attr_multi_option_field(attribute):
    return forms.ModelMultipleChoiceField(
        label=attribute.name,
        required=attribute.required,
        queryset=attribute.option_group.options.all())


def _attr_entity_field(attribute):
    # Product entities don't have out-of-the-box supported in the ProductForm.
    # There is no ModelChoiceField for generic foreign keys, and there's no
    # good default behaviour anyway; offering a choice of *all* model instances
    # is hardly useful.
    return None


def _attr_numeric_field(attribute):
    return forms.FloatField(label=attribute.name,
                            required=attribute.required)


def _attr_file_field(attribute):
    return forms.FileField(
        label=attribute.name, required=attribute.required)


def _attr_image_field(attribute):
    return forms.ImageField(
        label=attribute.name, required=attribute.required)


class ProductForm(forms.ModelForm):
    FIELD_FACTORIES = {
        "text": _attr_text_field,
        "richtext": _attr_textarea_field,
        "integer": _attr_integer_field,
        "boolean": _attr_boolean_field,
        "float": _attr_float_field,
        "date": _attr_date_field,
        "option": _attr_option_field,
        "multi_option": _attr_multi_option_field,
        "entity": _attr_entity_field,
        "numeric": _attr_numeric_field,
        "file": _attr_file_field,
        "image": _attr_image_field,
    }

    class Meta:
        model = Product
        fields = [
            'title', 'upc', 'description', 'is_discountable', 'structure']
        widgets = {
            'structure': forms.HiddenInput()
        }

    def __init__(self, product_class, data=None, parent=None, *args, **kwargs):
        self.set_initial(product_class, parent, kwargs)
        super(ProductForm, self).__init__(data, *args, **kwargs)
        if parent:
            self.instance.parent = parent
            # We need to set the correct product structures explicitly to pass
            # attribute validation and child product validation. Note that
            # those changes are not persisted.
            self.instance.structure = Product.CHILD
            self.instance.parent.structure = Product.PARENT

            self.delete_non_child_fields()
        else:
            # Only set product class for non-child products
            self.instance.product_class = product_class
        self.add_attribute_fields(product_class, self.instance.is_parent)

        if 'title' in self.fields:
            self.fields['title'].widget = forms.TextInput(
                attrs={'autocomplete': 'off'})

    def set_initial(self, product_class, parent, kwargs):
        """
        Set initial data for the form. Sets the correct product structure
        and fetches initial values for the dynamically constructed attribute
        fields.
        """
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        self.set_initial_attribute_values(product_class, kwargs)
        if parent:
            kwargs['initial']['structure'] = Product.CHILD

    def set_initial_attribute_values(self, product_class, kwargs):
        """
        Update the kwargs['initial'] value to have the initial values based on
        the product instance's attributes
        """
        instance = kwargs.get('instance')
        if instance is None:
            return
        for attribute in product_class.attributes.all():
            try:
                value = instance.attribute_values.get(
                    attribute=attribute).value
            except exceptions.ObjectDoesNotExist:
                pass
            else:
                kwargs['initial']['attr_%s' % attribute.code] = value

    def add_attribute_fields(self, product_class, is_parent=False):
        """
        For each attribute specified by the product class, this method
        dynamically adds form fields to the product form.
        """
        for attribute in product_class.attributes.all():
            field = self.get_attribute_field(attribute)
            if field:
                self.fields['attr_%s' % attribute.code] = field
                # Attributes are not required for a parent product
                if is_parent:
                    self.fields['attr_%s' % attribute.code].required = False

    def get_attribute_field(self, attribute):
        """
        Gets the correct form field for a given attribute type.
        """
        return self.FIELD_FACTORIES[attribute.type](attribute)

    def delete_non_child_fields(self):
        """
        Deletes any fields not needed for child products. Override this if
        you want to e.g. keep the description field.
        """
        for field_name in ['description', 'is_discountable']:
            if field_name in self.fields:
                del self.fields[field_name]

    def _post_clean(self):
        """
        Set attributes before ModelForm calls the product's clean method
        (which it does in _post_clean), which in turn validates attributes.
        """
        self.instance.attr.initiate_attributes()
        for attribute in self.instance.attr.get_all_attributes():
            field_name = 'attr_%s' % attribute.code
            # An empty text field won't show up in cleaned_data.
            if field_name in self.cleaned_data:
                value = self.cleaned_data[field_name]
                setattr(self.instance.attr, attribute.code, value)
        super(ProductForm, self)._post_clean()


class StockAlertSearchForm(forms.Form):
    status = forms.CharField(label=_('Status'))


class ProductCategoryForm(forms.ModelForm):

    class Meta:
        model = ProductCategory
        fields = ('category', )


BaseProductCategoryFormSet = inlineformset_factory(
    Product, ProductCategory, form=ProductCategoryForm, extra=1,
    can_delete=True)


class ProductCategoryFormSet(BaseProductCategoryFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        # This function just exists to drop the extra arguments
        super(ProductCategoryFormSet, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.instance.is_child and self.get_num_categories() == 0:
            raise forms.ValidationError(
                _("Stand-alone and parent products "
                  "must have at least one category"))
        if self.instance.is_child and self.get_num_categories() > 0:
            raise forms.ValidationError(
                _("A child product should not have categories"))

    def get_num_categories(self):
        num_categories = 0
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if (hasattr(form, 'cleaned_data')
                    and form.cleaned_data.get('category', None)
                    and not form.cleaned_data.get('DELETE', False)):
                num_categories += 1
        return num_categories


class ProductImageForm(forms.ModelForm):

    class Meta:
        model = ProductImage
        fields = ['product', 'original', 'caption']
        # use ImageInput widget to create HTML displaying the
        # actual uploaded image and providing the upload dialog
        # when clicking on the actual image.
        widgets = {
            'original': ImageInput(),
        }

    def save(self, *args, **kwargs):
        # We infer the display order of the image based on the order of the
        # image fields within the formset.
        kwargs['commit'] = False
        obj = super(ProductImageForm, self).save(*args, **kwargs)
        obj.display_order = self.get_display_order()
        obj.save()
        return obj

    def get_display_order(self):
        return self.prefix.split('-').pop()


BaseProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=2)


class ProductImageFormSet(BaseProductImageFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        super(ProductImageFormSet, self).__init__(*args, **kwargs)


class ProductRecommendationForm(forms.ModelForm):

    class Meta:
        model = ProductRecommendation
        fields = ['primary', 'recommendation', 'ranking']
        widgets = {
            'recommendation': ProductSelect,
        }

    def __init__(self, *args, **kwargs):
        super(ProductRecommendationForm, self).__init__(*args, **kwargs)
        self.fields['recommendation'].widget.attrs['class'] = "select2"


BaseProductRecommendationFormSet = inlineformset_factory(
    Product, ProductRecommendation, form=ProductRecommendationForm,
    extra=5, fk_name="primary")


class ProductRecommendationFormSet(BaseProductRecommendationFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        super(ProductRecommendationFormSet, self).__init__(*args, **kwargs)


class ProductClassForm(forms.ModelForm):

    class Meta:
        model = ProductClass
        fields = ['name', 'requires_shipping', 'track_stock', 'options']


class ProductAttributesForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProductAttributesForm, self).__init__(*args, **kwargs)

        # because we'll allow submission of the form with blank
        # codes so that we can generate them.
        self.fields["code"].required = False

        self.fields["option_group"].help_text = _("Select an option group")

    def clean_code(self):
        code = self.cleaned_data.get("code")
        title = self.cleaned_data.get("name")

        if not code and title:
            code = slugify(title)

        return code

    class Meta:
        model = ProductAttribute
        fields = ["name", "code", "type", "option_group", "required"]


ProductAttributesFormSet = inlineformset_factory(ProductClass,
                                                 ProductAttribute,
                                                 form=ProductAttributesForm,
                                                 extra=3)
