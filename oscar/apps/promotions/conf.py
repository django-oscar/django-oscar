from oscar.core.loading import get_classes

SingleProduct, RawHTML, Image, MultiImage, PagePromotion, \
        AutomaticProductList, HandPickedProductList = get_classes('promotions.models',
    ['SingleProduct', 'RawHTML', 'Image', 'MultiImage', 'PagePromotion',
     'AutomaticProductList', 'HandPickedProductList'])


def get_promotion_classes():
    return (RawHTML, Image, SingleProduct, AutomaticProductList,
            HandPickedProductList)


PROMOTION_POSITIONS = (('page', 'Page'),
                       ('right', 'Right-hand sidebar'),
                       ('left', 'Left-hand sidebar'))


PROMOTION_CLASSES = get_promotion_classes()
