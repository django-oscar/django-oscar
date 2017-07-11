from django.forms.models import inlineformset_factory

from oscar.core.loading import get_class, get_classes

HandPickedProductList, OrderedProduct \
    = get_classes('promotions.models',
                  ['HandPickedProductList', 'OrderedProduct'])
ProductSelect = get_class('dashboard.catalogue.widgets', 'ProductSelect')
OrderedProductForm = get_class('dashboard.promotions.forms', 'OrderedProductForm')

OrderedProductFormSet = inlineformset_factory(
    HandPickedProductList, OrderedProduct, form=OrderedProductForm, extra=2)
