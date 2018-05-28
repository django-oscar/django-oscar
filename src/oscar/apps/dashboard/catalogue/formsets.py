from django import forms
from django.core import exceptions
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_classes, get_model

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'StockRecord')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductImage = get_model('catalogue', 'ProductImage')
ProductRecommendation = get_model('catalogue', 'ProductRecommendation')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeOption = get_model('catalogue', 'AttributeOption')

(StockRecordForm,
 ProductCategoryForm,
 ProductImageForm,
 ProductRecommendationForm,
 ProductAttributesForm,
 AttributeOptionForm) = \
    get_classes('dashboard.catalogue.forms',
                ('StockRecordForm',
                 'ProductCategoryForm',
                 'ProductImageForm',
                 'ProductRecommendationForm',
                 'ProductAttributesForm',
                 'AttributeOptionForm'))


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

        super().__init__(*args, **kwargs)
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
        return super()._construct_form(
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


BaseProductCategoryFormSet = inlineformset_factory(
    Product, ProductCategory, form=ProductCategoryForm, extra=1,
    can_delete=True)


class ProductCategoryFormSet(BaseProductCategoryFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        # This function just exists to drop the extra arguments
        super().__init__(*args, **kwargs)

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


BaseProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=2)


class ProductImageFormSet(BaseProductImageFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)


BaseProductRecommendationFormSet = inlineformset_factory(
    Product, ProductRecommendation, form=ProductRecommendationForm,
    extra=5, fk_name="primary")


class ProductRecommendationFormSet(BaseProductRecommendationFormSet):

    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)


ProductAttributesFormSet = inlineformset_factory(ProductClass,
                                                 ProductAttribute,
                                                 form=ProductAttributesForm,
                                                 extra=3)


AttributeOptionFormSet = inlineformset_factory(AttributeOptionGroup,
                                               AttributeOption,
                                               form=AttributeOptionForm,
                                               extra=3)
