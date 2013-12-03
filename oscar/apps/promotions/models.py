from django.db.models import get_model

from oscar.apps.promotions.abstract_models import (
    AbstractPagePromotion, AbstractKeywordPromotion,
    AbstractRawHTML, AbstractImage, AbstractMultiImage,
    AbstractSingleProduct, AbstractHandPickedProductList,
    AbstractOrderedProduct, AbstractAutomaticProductList,
    AbstractOrderedProductList, AbstractTabbedBlock)

Item = get_model('product', 'Item')


# Linking models - these link promotions to content (eg pages, or keywords)


class PagePromotion(AbstractPagePromotion):
    pass


class KeywordPromotion(AbstractKeywordPromotion):
    pass


class RawHTML(AbstractRawHTML):
    pass


class Image(AbstractImage):
    pass


class MultiImage(AbstractMultiImage):
    pass


class SingleProduct(AbstractSingleProduct):
    pass


class HandPickedProductList(AbstractHandPickedProductList):
    pass


class OrderedProduct(AbstractOrderedProduct):
    pass


class AutomaticProductList(AbstractAutomaticProductList):
    pass


class OrderedProductList(AbstractOrderedProductList):
    pass


class TabbedBlock(AbstractTabbedBlock):
    pass
