from django import forms
from django.core.exceptions import ValidationError, MultipleObjectsReturned
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from treebeard.forms import MoveNodeForm, movenodeform_factory

from oscar.core.utils import slugify
from oscar.core.loading import get_class, get_model
from oscar.forms.widgets import ImageInput

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'StockRecord')
Partner = get_model('partner', 'Partner')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductImage = get_model('catalogue', 'ProductImage')
ProductRecommendation = get_model('catalogue', 'ProductRecommendation')
ProductSelect = get_class('dashboard.catalogue.widgets', 'ProductSelect')
ProductSelectMultiple = get_class('dashboard.catalogue.widgets',
                                  'ProductSelectMultiple')


class BaseCategoryForm(MoveNodeForm):

    def clean(self):
        cleaned_data = super(BaseCategoryForm, self).clean()

        name = cleaned_data.get('name')
        ref_node_pk = cleaned_data.get('_ref_node_id')
        pos = cleaned_data.get('_position')

        if name and self.is_slug_conflicting(name, ref_node_pk, pos):
            raise forms.ValidationError(
                _('Category with the given path already exists.'))
        return cleaned_data

    def is_slug_conflicting(self, name, ref_node_pk, position):
        # determine parent
        if ref_node_pk:
            ref_category = Category.objects.get(pk=ref_node_pk)
            if position == 'first-child':
                parent = ref_category
            else:
                parent = ref_category.get_parent()
        else:
            parent = None

        # build full slug
        slug_prefix = ''
        if parent:
            slug_prefix = (parent.slug + Category._slug_separator)
        slug = '%s%s' % (slug_prefix, slugify(name))

        # check if slug is conflicting
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            pass
        else:
            if category.pk != self.instance.pk:
                return True
        return False

CategoryForm = movenodeform_factory(Category, form=BaseCategoryForm)


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

        # If not tracking stock, we hide the fields
        if not product_class.track_stock:
            del self.fields['num_in_stock']
            del self.fields['low_stock_threshold']
        else:
            self.fields['price_excl_tax'].required = True
            self.fields['num_in_stock'].required = True

    class Meta:
        model = StockRecord
        exclude = ('product', 'num_allocated')


BaseStockRecordFormSet = inlineformset_factory(
    Product, StockRecord, form=StockRecordForm, extra=1)


class StockRecordFormSet(BaseStockRecordFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        self.user = user
        self.require_user_stockrecord = not user.is_staff
        self.product_class = product_class
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
            except (Partner.DoesNotExist, MultipleObjectsReturned):
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
                raise ValidationError(_("At least one stock record must be set"
                                        " to a partner that you're associated"
                                        " with."))


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
    return forms.ModelChoiceField(
        label=attribute.name,
        required=attribute.required,
        queryset=attribute.entity_type.entities.all())


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

    # We need a special field to distinguish between group and standalone
    # products.  It's impossible to tell when the product is first created.
    # This is quite clunky but will be replaced when #693 is complete.
    is_group = forms.BooleanField(
        label=_("Is group product?"),
        required=False,
        help_text=_(
            "Check this if this product is a group/parent product "
            "that has variants (eg different sizes/colours available)"))

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
        exclude = ('slug', 'product_class',
                   'recommended_products', 'product_options',
                   'attributes', 'categories')
        widgets = {
            'parent': ProductSelect,
        }

    def __init__(self, product_class, data=None, *args, **kwargs):
        self.set_initial_attribute_values(product_class, kwargs)
        super(ProductForm, self).__init__(data, *args, **kwargs)
        self.instance.product_class = product_class

        # Set the initial value of the is_group field.  This isn't watertight:
        # if the product is intended to be a parent product but doesn't have
        # any variants then we can't distinguish it from a standalone product
        # and this checkbox won't have the right value.  This will be addressed
        # in #693
        instance = kwargs.get('instance', None)
        if instance:
            self.fields['is_group'].initial = instance.is_group

        # This is quite nasty.  We use the raw posted data to determine if the
        # product is a group product, as this changes the validation rules we
        # want to apply.
        is_parent = data and data.get('is_group', '') == 'on'
        self.add_attribute_fields(is_parent)

        parent = self.fields.get('parent', None)

        if parent is not None:
            parent.queryset = self.get_parent_products_queryset()
        if 'title' in self.fields:
            self.fields['title'].widget = forms.TextInput(
                attrs={'autocomplete': 'off'})

    def set_initial_attribute_values(self, product_class, kwargs):
        """
        Update the kwargs['initial'] value to have the initial values based on
        the product instance's attributes
        """
        if kwargs.get('instance', None) is None:
            return
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        for attribute in product_class.attributes.all():
            try:
                value = kwargs['instance'].attribute_values.get(
                    attribute=attribute).value
            except ProductAttributeValue.DoesNotExist:
                pass
            else:
                kwargs['initial']['attr_%s' % attribute.code] = value

    def add_attribute_fields(self, is_parent=False):
        for attribute in self.instance.product_class.attributes.all():
            self.fields['attr_%s' % attribute.code] \
                = self.get_attribute_field(attribute)
            # Attributes are not required for a parent product
            if is_parent:
                self.fields['attr_%s' % attribute.code].required = False

    def get_attribute_field(self, attribute):
        return self.FIELD_FACTORIES[attribute.type](attribute)

    def get_parent_products_queryset(self):
        """
        :return: Canonical products excluding this product
        """
        # Not using Product.browsable because a deployment might override
        # that manager to respect a status field or such like
        queryset = Product._default_manager.filter(parent=None)
        if self.instance.pk is not None:
            # Prevent selecting itself as parent
            queryset = queryset.exclude(pk=self.instance.pk)
        return queryset

    def save(self):
        """
        Set product class and attributes before saving
        """
        product = super(ProductForm, self).save(commit=False)
        for attribute in self.instance.product_class.attributes.all():
            value = self.cleaned_data['attr_%s' % attribute.code]
            setattr(product.attr, attribute.code, value)
        product.save()
        self.save_m2m()
        return product


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
        if self.instance.is_top_level and self.get_num_categories() == 0:
            raise forms.ValidationError(
                _("A top-level product must have at least one category"))
        if self.instance.is_variant and self.get_num_categories() > 0:
            raise forms.ValidationError(
                _("A variant product should not have categories"))

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
        exclude = ('display_order',)
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
        widgets = {
            'recommendation': ProductSelect,
        }


BaseProductRecommendationFormSet = inlineformset_factory(
    Product, ProductRecommendation, form=ProductRecommendationForm,
    extra=5, fk_name="primary")


class ProductRecommendationFormSet(BaseProductRecommendationFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        super(ProductRecommendationFormSet, self).__init__(*args, **kwargs)


class ProductClassForm(forms.ModelForm):

    class Meta:
        model = ProductClass
