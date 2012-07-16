from django import forms
from django.forms.models import inlineformset_factory
from django.db.models import get_model
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from treebeard.forms import MoveNodeForm

Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'StockRecord')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductImage = get_model('catalogue', 'ProductImage')


class CategoryForm(MoveNodeForm):

    def clean(self):
        cleaned_data = super(CategoryForm, self).clean()

        name = cleaned_data['name']
        ref_node_pk = cleaned_data['_ref_node_id']
        pos = cleaned_data['_position']

        if name and self.is_slug_conflicting(name, ref_node_pk, pos):
            raise forms.ValidationError(_('Category with the given path'
                                                  ' already exists.'))
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
        slug_prefix = (parent.slug + Category._slug_separator) if parent else ''
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

    class Meta(MoveNodeForm.Meta):
        model = Category


class ProductSearchForm(forms.Form):
    upc = forms.CharField(max_length=16, required=False, label=_('UPC'))
    title = forms.CharField(max_length=255, required=False, label=_('Title'))


class StockRecordForm(forms.ModelForm):

    class Meta:
        model = StockRecord
        exclude = ('product', 'num_allocated', 'price_currency')


def _attr_text_field(attribute):
    return forms.CharField(label=attribute.name,
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


class ProductForm(forms.ModelForm):

    FIELD_FACTORIES = {
        "text": _attr_text_field,
        "richtext": _attr_text_field,
        "integer": _attr_integer_field,
        "boolean": _attr_boolean_field,
        "float": _attr_float_field,
        "date": _attr_date_field,
        "option": _attr_option_field,
        "multi_option" : _attr_multi_option_field,
        "entity": _attr_entity_field,
        "numeric" : _attr_numeric_field,
    }

    def __init__(self, product_class, *args, **kwargs):
        self.product_class = product_class
        self.set_initial_attribute_values(kwargs)
        super(ProductForm, self).__init__(*args, **kwargs)
        self.add_attribute_fields()

    def set_initial_attribute_values(self, kwargs):
        if kwargs.get('instance', None) is None:
            return
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        for attribute in self.product_class.attributes.all():
            try:
                value = kwargs['instance'].attribute_values.get(attribute=attribute).value
            except ProductAttributeValue.DoesNotExist:
                pass
            else:
                kwargs['initial']['attr_%s' % attribute.code] = value

    def add_attribute_fields(self):
        for attribute in self.product_class.attributes.all():
            self.fields['attr_%s' % attribute.code] = \
                    self.get_attribute_field(attribute)

    def get_attribute_field(self, attribute):
        return self.FIELD_FACTORIES[attribute.type](attribute)

    class Meta:
        model = Product
        exclude = ('slug', 'status', 'score', 'product_class',
                   'recommended_products', 'related_products',
                   'product_options', 'attributes', 'categories')

    def save(self):
        object = super(ProductForm, self).save(False)
        object.product_class = self.product_class
        for attribute in self.product_class.attributes.all():
            value = self.cleaned_data['attr_%s' % attribute.code]
            setattr(object.attr, attribute.code, value)
        if not object.upc:
            object.upc = None
        object.save()
        return object

    def save_attributes(self, object):
        for attribute in self.product_class.attributes.all():
            value = self.cleaned_data['attr_%s' % attribute.code]
            attribute.save_value(object, value)

    def clean(self):
        data = self.cleaned_data
        if data['parent'] is None and not data['title']:
            raise forms.ValidationError(_("Parent products must have a title"))
        return data


class StockAlertSearchForm(forms.Form):
    status = forms.CharField(label=_('Status'))


class ProductCategoryForm(forms.ModelForm):

    class Meta:
        model = ProductCategory


ProductCategoryFormSet = inlineformset_factory(Product, ProductCategory,
                                               form=ProductCategoryForm,
                                               fields=('category',), extra=1)


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('display_order',)

    def save(self, *args, **kwargs):
        # We infer the display order of the image based on the order of the image fields
        # within the formset.
        kwargs['commit'] = False
        obj = super(ProductImageForm, self).save(*args, **kwargs)
        obj.display_order = self.get_display_order()
        obj.save()
        return obj

    def get_display_order(self):
        return self.prefix.split('-').pop()



ProductImageFormSet = inlineformset_factory(Product, ProductImage,
                                            form=ProductImageForm,
                                            extra=2)
